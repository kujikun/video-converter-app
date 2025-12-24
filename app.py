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
    available_fonts = [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))]

# --- 1. メイン入力 ---
uploaded_file = st.file_uploader("動画ファイルを選択 (mp4, mov, avi)", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    # 一時ファイルとして保存
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    # 動画が変わったら状態リセット
    if 'current_video_path' not in st.session_state or st.session_state.current_video_path != video_path:
        st.session_state.current_video_path = video_path
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
        
        # --- 透かし機能 (強化版) ---
        enable_watermark = st.checkbox("透かし(文字)を入れる")
        wm_text = ""
        wm_font_path = None
        
        if enable_watermark:
            wm_text = st.text_input("透かし文字", "Sample")
            
            c1, c2 = st.columns(2)
            with c1:
                wm_color = st.color_picker("文字色", "#FFFFFF")
                # 位置選択機能を追加
                wm_position = st.selectbox("配置場所", ["右下", "左下", "左上", "右上", "中央"])
            with c2:
                wm_opacity = st.slider("不透明度", 0, 100, 100)
                # 縁取りオプションを追加
                wm_shadow = st.checkbox("文字に縁取り(影)を付ける", value=True)
            
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
        
        # --- サムネイル機能 (ロジック修正版) ---
        enable_thumb = st.checkbox("先頭にサムネイルを付ける")
        thumb_img_final = None 

        if enable_thumb:
            thumb_mode = st.radio("サムネ画像の指定", ["動画内のフレームを使用", "画像をアップロード"], horizontal=True)
            
            if thumb_mode == "動画内のフレームを使用":
                st.caption("スライダーで時間を選び、ボタンを押してください")
                
                # エラー回避のため上限を制限
                safe_max_duration = max(0.0, clip.duration - 0.2)
                thumb_time = st.slider("時間指定(秒)", 0.0, safe_max_duration, 0.0, 0.1)
                
                # ボタン処理
                if st.button("📸 フレームを取得・更新"):
                    try:
                        frame_at_time = clip.get_frame(thumb_time)
                        st.session_state.selected_thumb_img = Image.fromarray(frame_at_time)
                        st.rerun() # 即再読み込みして画面を更新
                    except Exception as e:
                        st.error(f"取得失敗: {e}")

                # 表示ロジックの整理（ここを修正）
                if st.session_state.selected_thumb_img is not None:
                    st.image(st.session_state.selected_thumb_img, caption="✅ セットされたサムネイル", width=200)
                    thumb_img_final = st.session_state.selected_thumb_img
                else:
                    st.info("👈 上のボタンを押して、サムネイル画像を確定させてください。")
                
            else:
                # アップロードモード
                thumb_file = st.file_uploader("画像をアップロード", type=["png", "jpg"])
                if thumb_file:
                    thumb_img_final = Image.open(thumb_file)

    # --- 実行ボタン ---
    st.markdown("---")
    
    ready_to_go = True
    if enable_thumb and thumb_img_final is None:
        ready_to_go = False
        st.warning("⚠️ サムネイル画像が決まっていません。")

    if ready_to_go and st.button("変換開始 (処理には少し時間がかかります)", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. リサイズ
            status_text.text("1/4 リサイズ中...")
            processed_clip = clip.resize(width=resize_width)
            progress_bar.progress(20)
            
            # 2. 透かし合成 (強化版)
            if enable_watermark and wm_text and wm_font_path:
                status_text.text("2/4 透かし合成中...")
                
                def add_watermark(frame):
                    pil_img = Image.fromarray(frame).convert("RGBA")
                    txt_layer = Image.new("RGBA", pil_img.size, (255, 255, 255, 0))
                    draw = ImageDraw.Draw(txt_layer)
                    
                    # フォントサイズ決定 (高さの1/8程度)
                    try:
                        font_size = int(pil_img.size[1] / 8) 
                        font = ImageFont.truetype(wm_font_path, font_size)
                    except:
                        font = ImageFont.load_default()
                    
                    # テキストサイズ計測
                    bbox = draw.textbbox((0, 0), wm_text, font=font)
                    text_w = bbox[2] - bbox[0]
                    text_h = bbox[3] - bbox[1]
                    
                    # 座標計算 (マージン20px)
                    margin = 20
                    W, H = pil_img.size
                    
                    if wm_position == "右下":
                        x, y = W - text_w - margin, H - text_h - margin
                    elif wm_position == "左下":
                        x, y = margin, H - text_h - margin
                    elif wm_position == "左上":
                        x, y = margin, margin
                    elif wm_position == "右上":
                        x, y = W - text_w - margin, margin
                    else: # 中央
                        x, y = (W - text_w) / 2, (H - text_h) / 2
                    
                    # 画面外にはみ出ないよう調整
                    x = max(0, min(x, W - text_w))
                    y = max(0, min(y, H - text_h))
                    
                    # 色設定
                    rgb = ImageColor.getrgb(wm_color)
                    fill_color = (rgb[0], rgb[1], rgb[2], int(255 * wm_opacity / 100))
                    
                    # 縁取り描画 (影)
                    if wm_shadow:
                        outline_color = (0, 0, 0, int(255 * wm_opacity / 100))
                        stroke_width = 2
                        # 文字の周りに少しずらして黒文字を描く
                        for adj_x in range(-stroke_width, stroke_width+1):
                            for adj_y in range(-stroke_width, stroke_width+1):
                                draw.text((x+adj_x, y+adj_y), wm_text, font=font, fill=outline_color)

                    # 本体描画
                    draw.text((x, y), wm_text, font=font, fill=fill_color)
                    
                    out = Image.alpha_composite(pil_img, txt_layer)
                    return np.array(out.convert("RGB"))

                processed_clip = processed_clip.fl_image(add_watermark)
            
            progress_bar.progress(50)

            # 3. サムネイル結合
            if enable_thumb and thumb_img_final:
                status_text.text("3/4 サムネイル結合中...")
                thumb_img = thumb_img_final.convert("RGB")
                aspect = thumb_img.height / thumb_img.width
                target_h = int(resize_width * aspect)
                thumb_img = thumb_img.resize((resize_width, target_h), Image.Resampling.LANCZOS)
                thumb_clip = ImageClip(np.array(thumb_img)).set_duration(0.1).set_fps(fps)
                processed_clip = concatenate_videoclips([thumb_clip, processed_clip], method="compose")
            
            progress_bar.progress(70)

            # 4. 書き出し
            status_text.text(f"4/4 {out_fmt}へ変換中...書き込みに時間がかかります")
            output_filename = f"output.{out_fmt.lower()}"
            
            if out_fmt == "WebP":
                processed_clip.write_videofile(
                    output_filename, 
                    fps=fps, 
                    codec='libwebp', 
                    ffmpeg_params=["-preset", "default", "-loop", "0"]
                )
            else:
                processed_clip.write_gif(output_filename, fps=fps)
            
            progress_bar.progress(100)
            status_text.success("変換完了！下のボタンからダウンロードしてください。")
            
            with open(output_filename, "rb") as f:
                btn = st.download_button(
                    label=f"📥 {out_fmt}をダウンロード",
                    data=f,
                    file_name=f"animation.{out_fmt.lower()}",
                    mime=f"image/{out_fmt.lower()}"
                )
            
            st.image(output_filename, caption="完成品プレビュー")

        except Exception as e:
            st.error(f"エラー詳細: {e}")
        finally:
            clip.close()
            if 'processed_clip' in locals(): processed_clip.close()

else:
    st.info("👆 動画をアップロードしてください")
