import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips, TextClip
from PIL import Image, ImageFont, ImageDraw
import numpy as np

# --- ページ設定 ---
st.set_page_config(page_title="動画GIF/WebP変換ツール", layout="centered")

st.title("🎥 動画 GIF/WebP 変換ツール")
st.markdown("""
動画ファイルをアップロードして、透かしやサムネイル付きのアニメーション画像を作成できます。
**(※推奨: 30秒以内、50MB以下の動画)**
""")

# --- 1. メイン入力 ---
uploaded_file = st.file_uploader("動画ファイルを選択 (mp4, mov, avi)", type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    # 一時ファイルとして保存
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    # 動画情報の取得
    try:
        clip = VideoFileClip(video_path)
        st.info(f"読み込み完了: {clip.duration:.1f}秒 / {clip.w}x{clip.h} / {clip.fps}fps")
    except Exception as e:
        st.error("動画の読み込みに失敗しました。")
        st.stop()

    # --- サイドバー設定 ---
    st.sidebar.header("🛠 変換設定")
    
    # 出力形式
    out_fmt = st.sidebar.radio("出力形式", ["GIF", "WebP"])
    
    # サイズと品質
    resize_width = st.sidebar.number_input("横幅リサイズ (px)", value=300, min_value=100, max_value=1280, step=10)
    fps = st.sidebar.slider("FPS (滑らかさ)", 1, 30, 10)
    
    # --- 2. 透かし機能 ---
    st.sidebar.markdown("---")
    st.sidebar.header("💧 透かし設定")
    enable_watermark = st.sidebar.checkbox("透かしを入れる")
    
    wm_text = ""
    wm_font_file = None
    wm_color = "#FFFFFF"
    wm_opacity = 100
    
    if enable_watermark:
        wm_text = st.sidebar.text_input("透かし文字", "Sample")
        wm_color = st.sidebar.color_picker("文字色", "#FFFFFF")
        wm_opacity = st.sidebar.slider("不透明度", 0, 100, 80)
        # Web上にはフォントがないため、アップロードしてもらうのが確実
        wm_font_file = st.sidebar.file_uploader("フォントファイル (.ttf) を選択", type=["ttf", "otf"], help="日本語を表示するには日本語フォントが必要です")
        
    # --- 3. サムネイル挿入機能 ---
    st.sidebar.markdown("---")
    st.sidebar.header("🖼 サムネイル設定")
    enable_thumb = st.sidebar.checkbox("先頭にサムネイル画像を挿入")
    thumb_file = None
    if enable_thumb:
        thumb_file = st.sidebar.file_uploader("サムネイル画像を選択", type=["png", "jpg", "jpeg"])

    # --- 実行ボタン ---
    st.markdown("---")
    if st.button("変換を実行する", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 1. リサイズ処理
            status_text.text("リサイズ中...")
            processed_clip = clip.resize(width=resize_width)
            
            # 2. 透かし処理
            if enable_watermark and wm_text and wm_font_file:
                status_text.text("透かし合成中...")
                
                # フォントの一時保存
                font_path = "temp_font.ttf"
                with open(font_path, "wb") as f:
                    f.write(wm_font_file.read())
                
                # Pillowを使って画像として透かしを作成
                def add_watermark(frame):
                    pil_img = Image.fromarray(frame).convert("RGBA")
                    txt_layer = Image.new("RGBA", pil_img.size, (255, 255, 255, 0))
                    draw = ImageDraw.Draw(txt_layer)
                    
                    try:
                        font_size = int(pil_img.size[1] / 10) # 高さの1/10
                        font = ImageFont.truetype(font_path, font_size)
                    except:
                        font = ImageFont.load_default()
                    
                    # テキストサイズ取得
                    bbox = draw.textbbox((0, 0), wm_text, font=font)
                    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    
                    # 右下に配置
                    x = pil_img.size[0] - text_w - 10
                    y = pil_img.size[1] - text_h - 10
                    
                    # 色変換
                    from PIL import ImageColor
                    rgb = ImageColor.getrgb(wm_color)
                    color = (rgb[0], rgb[1], rgb[2], int(255 * wm_opacity / 100))
                    
                    draw.text((x, y), wm_text, font=font, fill=color)
                    out = Image.alpha_composite(pil_img, txt_layer)
                    return np.array(out.convert("RGB"))

                processed_clip = processed_clip.fl_image(add_watermark)

            # 3. サムネイル結合
            if enable_thumb and thumb_file:
                status_text.text("サムネイル結合中...")
                thumb_img = Image.open(thumb_file).convert("RGB")
                
                # 動画の幅に合わせてリサイズ
                aspect = thumb_img.height / thumb_img.width
                target_h = int(resize_width * aspect)
                thumb_img = thumb_img.resize((resize_width, target_h), Image.Resampling.LANCZOS)
                
                # 画像をクリップ化 (0.1秒など短く表示するか、1秒表示するか)
                thumb_clip = ImageClip(np.array(thumb_img)).set_duration(0.1).set_fps(fps)
                
                # 結合
                processed_clip = concatenate_videoclips([thumb_clip, processed_clip], method="compose")

            # 4. 書き出し
            status_text.text(f"{out_fmt}へ変換中... (時間がかかります)")
            output_filename = f"output.{out_fmt.lower()}"
            
            # WebPとGIFで書き分け
            if out_fmt == "WebP":
                # WebPはファイルサイズが大きくなりがちなので画質調整が必要かもしれません
                processed_clip.write_videofile(output_filename, fps=fps, codec='libwebp', logger=None)
            else:
                processed_clip.write_gif(output_filename, fps=fps, logger=None)
            
            progress_bar.progress(100)
            status_text.text("完了！")
            
            # 5. ダウンロードボタン表示
            with open(output_filename, "rb") as file:
                btn = st.download_button(
                    label=f"📥 {out_fmt}ファイルをダウンロード",
                    data=file,
                    file_name=f"animation.{out_fmt.lower()}",
                    mime=f"image/{out_fmt.lower()}"
                )
                
            # プレビュー表示
            st.image(output_filename, caption="変換結果プレビュー")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
        finally:
            # クリーンアップ
            clip.close()
            if 'processed_clip' in locals(): processed_clip.close()

else:
    st.info("左上の「Browse files」から動画をアップロードしてください。")