import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageFont, ImageDraw, ImageColor
import numpy as np

# --- ページ設定 ---
st.set_page_config(page_title="動画GIF/WebP変換ツール", layout="wide", page_icon="🎥")

# --- カスタムCSS (UIを整える) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .stExpander { border: 1px solid #e6e9ef; border-radius: 5px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- サイドバー (説明書) ---
with st.sidebar:
    st.title("📖 使い方ガイド")
    st.info("""
    1. **動画をアップ**: 中央のエリアにファイルをドラッグ。
    2. **設定**: 出力形式やリサイズ幅を決める。
    3. **透かし/サムネ**: 必要に応じて設定。
    4. **確定ボタン**: サムネを使う場合は必ず「確定ボタン」を押す。
    5. **変換**: 最後に「変換開始」をクリック！
    """)
    st.divider()
    st.caption("© 2024 動画変換ツール制作プロジェクト")

# --- メインレイアウト ---
st.title("🎥 動画 GIF/WebP 変換プロ")
st.write("ブログ掲載用に最適化された高機能コンバーターです。")

# --- フォント準備 ---
FONTS_DIR = "fonts"
available_fonts = []
if os.path.exists(FONTS_DIR):
    available_fonts = sorted([f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))])

# --- 1. ファイルアップロード ---
uploaded_file = st.file_uploader("動画ファイルを選択 (mp4, mov, avi)", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    if 'last_video_name' not in st.session_state or st.session_state.last_video_name != uploaded_file.name:
        st.session_state.last_video_name = uploaded_file.name
        st.session_state.selected_thumb_img = None
    
    try:
        clip = VideoFileClip(video_path)
        
        # プレビューと情報の並列表示
        col_pre1, col_pre2 = st.columns([2, 1])
        with col_pre1:
            st.video(video_path)
        with col_pre2:
            st.metric("動画の長さ", f"{clip.duration:.1f} 秒")
            st.metric("元の解像度", f"{clip.w} x {clip.h}")
            
    except Exception as e:
        st.error(f"動画の読み込みに失敗しました: {e}")
        st.stop()

    # --- 2. 各種設定エリア ---
    with st.expander("⚙️ 基本変換設定", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            out_fmt = st.selectbox("出力形式", ["GIF", "WebP"])
        with c2:
            resize_width = st.number_input("横幅リサイズ (px)", value=300, step=50)
        with c3:
            fps = st.slider("FPS (滑らかさ)", 5, 30, 10)

    with st.expander("✒️ 透かし文字の設定"):
        enable_watermark = st.checkbox("透かしを入れる")
        if enable_watermark:
            wm_text = st.text_input("表示テキスト", "Sample Copy")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                wm_color = st.color_picker("文字色", "#FFFFFF")
                wm_position = st.selectbox("配置場所", ["右下", "左下", "左上", "右上", "中央"])
            with c2:
                wm_size = st.slider("文字サイズ", 10, 200, 40)
                wm_opacity = st.slider("不透明度", 0, 100, 100)
            with c3:
                wm_shadow = st.checkbox("縁取り(影)を付ける", value=True)
                font_source = st.radio("フォント", ["リスト", "アップロード"], horizontal=True)

            if font_source == "リスト":
                wm_font_path = os.path.join(FONTS_DIR, st.selectbox("フォント選択", available_fonts)) if available_fonts else None
            else:
                f_file = st.file_uploader("TTF/OTF", type=["ttf", "otf"])
                if f_file:
                    with open("temp_f.ttf", "wb") as f: f.write(f_file.read())
                    wm_font_path = "temp_f.ttf"
                else: wm_font_path = None

    with st.expander("🖼 サムネイル(先頭フレーム)の設定"):
        enable_thumb = st.checkbox("先頭に静止画を入れる")
        thumb_img_final = None
        if enable_thumb:
            t_mode = st.radio("モード", ["動画から抽出", "画像をアップロード"], horizontal=True)
            if t_mode == "動画から抽出":
                t_time = st.slider("抽出時間(秒)", 0.0, max(0.0, clip.duration-0.2), 0.0, 0.1)
                if st.button("📸 この瞬間をサムネイルとして確定する"):
                    st.session_state.selected_thumb_img = Image.fromarray(clip.get_frame(t_time))
                    st.rerun()
                
                if st.session_state.selected_thumb_img:
                    st.success("✅ サムネイル取得済み")
                    st.image(st.session_state.selected_thumb_img, width=200)
                    thumb_img_final = st.session_state.selected_thumb_img
                else:
                    st.warning("画像が確定していません。上のボタンを押してください。")
            else:
                f_thumb = st.file_uploader("画像選択", type=["png", "jpg"])
                if f_thumb: thumb_img_final = Image.open(f_thumb)

    # --- 3. 実行セクション ---
    st.markdown("---")
    ready = not (enable_thumb and thumb_img_final is None)
    
    if not ready:
        st.error("サムネイル画像が確定していないため、変換を開始できません。")
    
    if st.button("🚀 変換を開始する", type="primary", disabled=not ready):
        prog = st.progress(0)
        status = st.empty()
        try:
            # 1. リサイズ
            status.text("リサイズ処理中...")
            processed = clip.resize(width=resize_width)
            prog.progress(25)
            
            # 2. 透かし
            if enable_watermark and wm_text and wm_font_path:
                status.text("透かしを合成中...")
                def draw_wm(frame):
                    img = Image.fromarray(frame).convert("RGBA")
                    txt = Image.new("RGBA", img.size, (255,255,255,0))
                    d = ImageDraw.Draw(txt)
                    try: fnt = ImageFont.truetype(wm_font_path, wm_size)
                    except: fnt = ImageFont.load_default()
                    
                    b = d.textbbox((0,0), wm_text, font=fnt)
                    tw, th = b[2]-b[0], b[3]-b[1]
                    m = 20
                    W, H = img.size
                    if wm_position == "右下": x, y = W-tw-m, H-th-m
                    elif wm_position == "左下": x, y = m, H-th-m
                    elif wm_position == "左上": x, y = m, m
                    elif wm_position == "右上": x, y = W-tw-m, m
                    else: x, y = (W-tw)/2, (H-th)/2
                    
                    rgb = ImageColor.getrgb(wm_color)
                    fill = (rgb[0], rgb[1], rgb[2], int(255*wm_opacity/100))
                    if wm_shadow:
                        shd = (0,0,0,int(255*wm_opacity/100))
                        for ax in range(-2,3):
                            for ay in range(-2,3): d.text((x+ax, y+ay), wm_text, font=fnt, fill=shd)
                    d.text((x,y), wm_text, font=fnt, fill=fill)
                    return np.array(Image.alpha_composite(img, txt).convert("RGB"))
                processed = processed.fl_image(draw_wm)
            prog.progress(50)

            # 3. サムネ結合
            if enable_thumb and thumb_img_final:
                status.text("サムネイルを結合中...")
                t_img = thumb_img_final.convert("RGB")
                th_h = int(resize_width * (t_img.height / t_img.width))
                t_img = t_img.resize((resize_width, th_h), Image.Resampling.LANCZOS)
                t_clip = ImageClip(np.array(t_img)).set_duration(0.1).set_fps(fps)
                processed = concatenate_videoclips([t_clip, processed], method="compose")
            prog.progress(75)

            # 4. 書き出し
            status.text(f"{out_fmt} 変換中...（これには時間がかかります）")
            out_name = f"output.{out_fmt.lower()}"
            if out_fmt == "WebP":
                # method=0 で高速化, qualityを指定してバランス調整
                processed.write_videofile(out_name, fps=fps, codec='libwebp', 
                                          ffmpeg_params=["-preset", "default", "-loop", "0", "-qscale", "80", "-method", "0"])
            else:
                processed.write_gif(out_name, fps=fps)
            
            prog.progress(100)
            status.success("✨ 変換が完了しました！")
            
            with open(out_name, "rb") as f:
                st.download_button(f"📥 {out_fmt}を保存する", f, file_name=f"converted.{out_fmt.lower()}")
            st.image(out_name, caption="完成プレビュー")

        except Exception as e:
            st.error(f"変換エラー: {e}")
        finally:
            clip.close()
            if 'processed' in locals(): processed.close()
else:
    st.info("まずは動画ファイルをアップロードしてください。左側に使い方のヒントがあります。")
