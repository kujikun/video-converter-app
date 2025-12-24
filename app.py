import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageFont, ImageDraw, ImageColor
import numpy as np

# --- ページ設定 ---
st.set_page_config(page_title="動画GIF/WebP変換ツール", layout="centered")
st.title("🎥 動画 GIF/WebP 変換ツール")

# --- フォントの準備 ---
FONTS_DIR = "fonts"
available_fonts = []
if os.path.exists(FONTS_DIR):
    available_fonts = sorted([f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))])

# --- 1. メイン入力 ---
uploaded_file = st.file_uploader("動画ファイルを選択 (mp4, mov, avi)", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    # 一時ファイルとして保存
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    # 動画が変わったら状態リセット
    if 'last_video_name' not in st.session_state or st.session_state.last_video_name != uploaded_file.name:
        st.session_state.last_video_name = uploaded_file.name
        st.session_state.selected_thumb_img = None
    
    try:
        clip = VideoFileClip(video_path)
        st.video(video_path)
        st.info(f"動画情報: {clip.duration:.1f}秒 / {clip.w}x{clip.h}")
    except Exception as e:
        st.error("動画の読み込みに失敗しました。")
        st.stop()

    # --- 設定エリア ---
    with st.expander("🛠 変換・サムネ・透かし設定", expanded=True):
        
        col1, col2 = st.columns(2)
        with col1:
            out_fmt = st.radio("出力形式", ["GIF", "WebP"])
            resize_width = st.number_input("横幅リサイズ (px)", value=300, step=50)
        with col2:
            fps = st.slider("FPS (滑らかさ)", 5, 30, 10)
            
        st.markdown("---")
        
        # --- 透かし機能 (サイズ変更追加) ---
        enable_watermark = st.checkbox("透かし(文字)を入れる")
        wm_text = ""
        wm_font_path = None
        
        if enable_watermark:
            wm_text = st.text_input("透かし文字", "Sample")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                wm_color = st.color_picker("文字色", "#FFFFFF")
                wm_position = st.selectbox("配置場所", ["右下", "左下", "左上", "右上", "中央"])
            with c2:
                wm_opacity = st.slider("不透明度", 0, 100, 100)
                wm_size = st.slider("文字サイズ", 10, 200, 40) # サイズ変更機能
            with c3:
                wm_shadow = st.checkbox("縁取り(影)付", value=True)
            
            font_source = st.radio("フォント選択", ["リストから選択", "アップロード"], horizontal=True)
            
            if font_source == "リストから選択":
                if available_fonts:
                    selected_font_name = st.selectbox("使用するフォント", available_fonts)
                    wm_font_path = os.path.join(FONTS_DIR, selected_font_name)
                else:
                    st.warning(f"⚠️ '{FONTS_DIR}' フォルダにフォントが見つかりません。")
            else:
                uploaded_font = st.file_uploader("フォントファイル(.ttf)", type=["ttf", "otf"])
                if uploaded_font:
                    with open("temp_user_font.ttf", "wb") as f:
                        f.write(uploaded_font.read())
                    wm_font_path = "temp_user_font.ttf"

        st.markdown("---")
        
        # --- サムネイル機能 (記憶保持を強化) ---
        enable_thumb = st.checkbox("先頭にサムネイルを付ける")
        thumb_img_final = None 

        if enable_thumb:
            thumb_mode = st.radio("サムネ画像の指定", ["動画内のフレームを使用", "画像をアップロード"], horizontal=True)
            
            if thumb_mode == "動画内のフレームを使用":
                st.caption("スライダーで時間を選び、ボタンを押してください")
                safe_max_duration = max(0.0, clip.duration - 0.2)
                thumb_time = st.slider("時間指定(秒)", 0.0, safe_max_duration, 0.0, 0.1)
                
                if st.button("📸 このフレームをサムネイルに確定する"):
                    try:
                        frame = clip.get_frame(thumb_time)
                        # 確実にセッションに保存
                        st.session_state.selected_thumb_img = Image.fromarray(frame)
                        st.rerun() 
                    except Exception as e:
                        st.error(f"取得失敗: {e}")

                # 判定: セッションに画像があるか？
                if st.session_state.selected_thumb_img is not None:
                    st.image(st.session_state.selected_thumb_img, caption="✅ サムネイルが確定しました", width=200)
                    thumb_img_final = st.session_state.selected_thumb_img
                else:
                    st.info("👈 上のボタンを押して、画像を確定させてください。")
                
            else:
                thumb_file = st.file_uploader("画像をアップロード", type=["png", "jpg"])
                if thumb_file:
                    thumb_img_final = Image.open(thumb_file)

    # --- 実行ボタン ---
    st.markdown("---")
    
    ready_to_go = True
    if enable_thumb and thumb_img_final is None:
        ready_to_go = False
        st.warning("⚠️ サムネイル画像が確定していません。")

    if ready_to_go and st.button("変換開始 (処理開始まで数秒かかります)", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. リサイズ
            status_text.text("1/4 リサイズ中...")
            processed_clip = clip.resize(width=resize_width)
            progress_bar.progress(20)
            
            # 2. 透かし合成
            if enable_watermark and wm_text and wm_font_path:
                status_text.text("2/4 透かし合成中...")
                
                def add_watermark(frame):
                    pil_img = Image.fromarray(frame).convert("RGBA")
                    txt_layer = Image.new("RGBA", pil_img.size, (255, 255, 255, 0))
                    draw = ImageDraw.Draw(txt_layer)
                    
                    try:
                        font = ImageFont.truetype(wm_font_path, wm_size)
                    except:
                        font = ImageFont.load_default()
                    
                    bbox = draw.textbbox((0, 0), wm_text, font=font)
                    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    margin = 20
                    W, H = pil_img.size
                    
                    if wm_position == "右下": x, y = W - text_w - margin, H - text_h - margin
                    elif wm_position == "左下": x, y = margin, H - text_h - margin
                    elif wm_position == "左上": x, y = margin, margin
                    elif wm_position == "右上": x, y = W - text_w - margin, margin
                    else: x, y = (W - text_w) / 2, (H - text_h) / 2
                    
                    x, y = max(0, min(x, W - text_w)), max(0, min(y, H - text_h))
                    
                    rgb = ImageColor.getrgb(wm_color)
                    fill_c = (rgb[0], rgb[1], rgb[2], int(255 * wm_opacity / 100))
                    
                    if wm_shadow:
                        sha_c = (0, 0, 0, int(255 * wm_opacity / 100))
                        sw = 2
                        for ax in range(-sw, sw+1):
                            for ay in range(-sw, sw+1):
                                draw.text((x+ax, y+ay), wm_text, font=font, fill=sha_c)

                    draw.text((x, y), wm_text, font=font, fill=fill_c)
                    return np.array(Image.alpha_composite(pil_img, txt_layer).convert("RGB"))

                processed_clip = processed_clip.fl_image(add_watermark)
            
            progress_bar.progress(50)

            # 3. サムネイル結合
            if enable_thumb and thumb_img_final:
                status_text.text("3/4 サムネイル結合中...")
                t_img = thumb_img_final.convert("RGB")
                target_h = int(resize_width * (t_img.height / t_img.width))
                t_img = t_img.resize((resize_width, target_h), Image.Resampling.LANCZOS)
                t_clip = ImageClip(np.array(t_img)).set_duration(0.1).set_fps(fps)
                processed_clip = concatenate_videoclips([t_clip, processed_clip], method="compose")
            
            progress_bar.progress(70)

            # 4. 書き出し
            status_text.text(f"4/4 {out_fmt}へ変換中...")
            out_file = f"output.{out_fmt.lower()}"
            if out_fmt == "WebP":
                processed_clip.write_videofile(out_file, fps=fps, codec='libwebp', ffmpeg_params=["-preset", "default", "-loop", "0"])
            else:
                processed_clip.write_gif(out_file, fps=fps)
            
            progress_bar.progress(100)
            status_text.success("完了！")
            
            with open(out_file, "rb") as f:
                st.download_button(f"📥 {out_fmt}をダウンロード", f, file_name=f"result.{out_fmt.lower()}", mime=f"image/{out_fmt.lower()}")
            st.image(out_file)

        except Exception as e:
            st.error(f"エラー: {e}")
        finally:
            clip.close()
            if 'processed_clip' in locals(): processed_clip.close()
