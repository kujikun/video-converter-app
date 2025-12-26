import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageFont, ImageDraw, ImageColor
import numpy as np

# --- ページ設定 ---
st.set_page_config(page_title="動画GIF/WebP変換プロ", layout="wide", page_icon="🎥")

# --- サイドバー ---
with st.sidebar:
    st.title("📖 使い方ガイド")
    st.info("""
    1. **動画をアップ**: 中央にファイルを置く。
    2. **カット**: 必要な範囲を秒数で指定。
    3. **設定**: 形式やサイズを決定。
    4. **透かし**: 最大3つまで設定可能。
    5. **確定**: サムネを使うなら必ず「確定」を押す。
    6. **実行**: 「変換を開始」をクリック。
    """)
    st.divider()
    st.caption("© 2024 動画変換ツール")

# --- フォント準備 ---
FONTS_DIR = "fonts"
available_fonts = []
if os.path.exists(FONTS_DIR):
    available_fonts = sorted([f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))])

# --- メイン画面 ---
st.title("🎥 動画 GIF/WebP 変換プロ (多機能版)")

uploaded_file = st.file_uploader("動画ファイルを選択", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    if 'last_video_name' not in st.session_state or st.session_state.last_video_name != uploaded_file.name:
        st.session_state.last_video_name = uploaded_file.name
        st.session_state.selected_thumb_img = None
    
    try:
        clip = VideoFileClip(video_path)
        col_pre1, col_pre2 = st.columns([2, 1])
        with col_pre1:
            st.video(video_path)
        with col_pre2:
            st.metric("動画の長さ", f"{clip.duration:.1f} 秒")
            st.metric("元の解像度", f"{clip.w} x {clip.h}")
            
    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        st.stop()

    # --- 各種設定 ---
    with st.expander("✂️ 動画のカット (トリミング)"):
        c_cut1, c_cut2 = st.columns(2)
        start_t = c_cut1.number_input("開始時間 (秒)", 0.0, clip.duration, 0.0, 0.1)
        end_t = c_cut2.number_input("終了時間 (秒)", 0.0, clip.duration, clip.duration, 0.1)
        if start_t >= end_t:
            st.warning("開始時間は終了時間より前に設定してください。")

    with st.expander("⚙️ 基本変換設定"):
        c1, c2, c3 = st.columns(3)
        out_fmt = c1.selectbox("出力形式", ["GIF", "WebP"])
        resize_width = c2.number_input("横幅リサイズ (px)", 100, 2000, 300)
        fps = c3.slider("FPS", 5, 30, 10)

    with st.expander("✒️ 透かし文字の設定 (最大3つ)"):
        wm_configs = []
        tabs = st.tabs(["透かし 1", "透かし 2", "透かし 3"])
        
        for i, tab in enumerate(tabs):
            with tab:
                enabled = st.checkbox(f"透かし {i+1} を有効にする", key=f"en_{i}")
                if enabled:
                    txt = st.text_input("表示テキスト", f"Text {i+1}", key=f"txt_{i}")
                    c_wm1, c_wm2, c_wm3 = st.columns(3)
                    with c_wm1:
                        pos = st.selectbox("位置", ["右下", "左下", "左上", "右上", "中央"], key=f"pos_{i}")
                        color = st.color_picker("色", "#FFFFFF", key=f"col_{i}")
                    with c_wm2:
                        size = st.slider("サイズ", 10, 200, 40, key=f"size_{i}")
                        opacity = st.slider("不透明度", 0, 100, 100, key=f"op_{i}")
                    with c_wm3:
                        shadow = st.checkbox("縁取り", value=True, key=f"shd_{i}")
                        fnt_src = st.radio("フォント", ["リスト", "アップロード"], horizontal=True, key=f"fsrc_{i}")
                    
                    f_path = None
                    if fnt_src == "リスト":
                        if available_fonts:
                            f_path = os.path.join(FONTS_DIR, st.selectbox("フォント選択", available_fonts, key=f"fsel_{i}"))
                    else:
                        f_file = st.file_uploader("TTF/OTF", type=["ttf", "otf"], key=f"fup_{i}")
                        if f_file:
                            f_path = f"temp_f_{i}.ttf"
                            with open(f_path, "wb") as f: f.write(f_file.read())
                    
                    wm_configs.append({
                        "text": txt, "pos": pos, "color": color, 
                        "size": size, "opacity": opacity, "shadow": shadow, "font": f_path
                    })

    with st.expander("🖼 サムネイル(先頭フレーム)の設定"):
        enable_thumb = st.checkbox("先頭に静止画を結合")
        thumb_img_final = None
        if enable_thumb:
            t_mode = st.radio("選択モード", ["動画から抽出", "画像をアップロード"], horizontal=True)
            if t_mode == "動画から抽出":
                t_time = st.slider("抽出秒数", 0.0, max(0.0, clip.duration-0.2), 0.0, 0.1)
                if st.button("📸 この瞬間をサムネイルにする"):
                    st.session_state.selected_thumb_img = Image.fromarray(clip.get_frame(t_time))
                    st.rerun()
                if st.session_state.selected_thumb_img:
                    st.image(st.session_state.selected_thumb_img, width=200)
                    thumb_img_final = st.session_state.selected_thumb_img
            else:
                f_thumb = st.file_uploader("画像選択", type=["png", "jpg"])
                if f_thumb: thumb_img_final = Image.open(f_thumb)

    # --- 実行セクション ---
    st.markdown("---")
    if st.button("🚀 変換を開始する", type="primary"):
        prog = st.progress(0)
        status = st.empty()
        try:
            # 1. カット
            status.text("動画をカット中...")
            processed = clip.subclip(start_t, end_t)
            prog.progress(10)
            
            # 2. リサイズ
            status.text("リサイズ中...")
            processed = processed.resize(width=resize_width)
            prog.progress(30)
            
            # 3. 複数透かしの合成
            if wm_configs:
                status.text("複数の透かしを合成中...")
                def draw_all_wm(frame):
                    img = Image.fromarray(frame).convert("RGBA")
                    for wm in wm_configs:
                        txt_layer = Image.new("RGBA", img.size, (255,255,255,0))
                        d = ImageDraw.Draw(txt_layer)
                        try: fnt = ImageFont.truetype(wm["font"], wm["size"]) if wm["font"] else ImageFont.load_default()
                        except: fnt = ImageFont.load_default()
                        
                        b = d.textbbox((0,0), wm["text"], font=fnt)
                        tw, th, m = b[2]-b[0], b[3]-b[1], 20
                        W, H = img.size
                        if wm["pos"] == "右下": x, y = W-tw-m, H-th-m
                        elif wm["pos"] == "左下": x, y = m, H-th-m
                        elif wm["pos"] == "左上": x, y = m, m
                        elif wm["pos"] == "右上": x, y = W-tw-m, m
                        else: x, y = (W-tw)/2, (H-th)/2
                        
                        rgb = ImageColor.getrgb(wm["color"])
                        fill = (rgb[0], rgb[1], rgb[2], int(255*wm["opacity"]/100))
                        if wm["shadow"]:
                            shd = (0,0,0,int(255*wm["opacity"]/100))
                            for ax in range(-2,3):
                                for ay in range(-2,3): d.text((x+ax, y+ay), wm["text"], font=fnt, fill=shd)
                        d.text((x,y), wm["text"], font=fnt, fill=fill)
                        img = Image.alpha_composite(img, txt_layer)
                    return np.array(img.convert("RGB"))
                processed = processed.fl_image(draw_all_wm)
            prog.progress(50)

            # 4. サムネ結合
            if enable_thumb and thumb_img_final:
                status.text("サムネイルを結合中...")
                t_img = thumb_img_final.convert("RGB")
                th_h = int(resize_width * (t_img.height / t_img.width))
                t_img = t_img.resize((resize_width, th_h), Image.Resampling.LANCZOS)
                t_clip = ImageClip(np.array(t_img)).set_duration(0.1).set_fps(fps)
                processed = concatenate_videoclips([t_clip, processed], method="compose")
            prog.progress(70)

            # 5. 書き出し
            status.text(f"{out_fmt} 変換中...")
            out_name = f"output.{out_fmt.lower()}"
            if out_fmt == "WebP":
                processed.write_videofile(out_name, fps=fps, codec='libwebp', 
                                          ffmpeg_params=["-preset", "default", "-loop", "0", "-qscale", "80", "-method", "0"])
            else:
                processed.write_gif(out_name, fps=fps)
            
            prog.progress(100)
            status.success("✨ 完了しました！")
            with open(out_name, "rb") as f:
                st.download_button(f"📥 {out_fmt}を保存", f, file_name=f"result.{out_fmt.lower()}")
            st.image(out_name)
        except Exception as e: st.error(f"エラー: {e}")
        finally:
            clip.close()
            if 'processed' in locals(): processed.close()
