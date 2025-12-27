import streamlit as st
import tempfile
import os
import shutil
import zipfile
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageFont, ImageDraw, ImageColor
import numpy as np

# --- 言語設定辞書 (大幅追加) ---
LANGUAGES = {
    "日本語": {
        "title": "V-Convert Pro (多機能メディア変換)",
        # サイドバー
        "mode_select": "機能モード選択",
        "mode_anim": "🎬 アニメーション変換 (GIF/WebP)",
        "mode_image": "📷 静止画抽出 (PNG/JPG)",
        "guide": "📖 使い方ガイド",
        "guide_anim": """
        **[アニメーション変換モード]**
        1. 動画をアップロード
        2. 必要ならカット範囲を指定
        3. 出力形式やサイズを設定
        4. 透かしを設定（最大3つ）
        5. サムネを使う場合は「確定」を押す
        6. 「変換を開始」をクリック
        """,
        "guide_image": """
        **[静止画抽出モード]**
        1. 動画をアップロード
        2. 抽出モードを選択（枚数指定 or 間隔指定）
        3. 出力形式（JPEG推奨）と品質を設定
        4. 透かしを設定（すべての画像に入ります）
        5. 「抽出を開始」をクリック
        6. ZIPファイルをダウンロード
        """,
        # 共通
        "upload_label": "動画ファイルを選択",
        "video_info": "動画情報",
        "duration": "長さ",
        "resolution": "元の解像度",
        "wm_section": "✒️ 透かし文字の設定 (最大3つ)",
        "wm_enable": "有効にする",
        "wm_text": "表示テキスト",
        "wm_pos": "位置",
        "wm_color": "色",
        "wm_size": "サイズ",
        "wm_opacity": "不透明度",
        "wm_shadow": "縁取り",
        "font_src": "フォント",
        "font_list": "リスト",
        "font_upload": "アップロード",
        "pos_opts": ["右下", "左下", "左上", "右上", "中央"],
        # アニメーション用
        "anim_title": "🎬 アニメーション作成設定",
        "cut_section": "✂️ 動画のカット (トリミング)",
        "start_time": "開始時間 (秒)",
        "end_time": "終了時間 (秒)",
        "basic_settings": "⚙️ 基本変換設定",
        "output_format": "出力形式",
        "resize_width": "横幅リサイズ (px)",
        "fps": "FPS (滑らかさ)",
        "thumb_section": "🖼 サムネイル(先頭フレーム)の設定",
        "thumb_enable": "先頭に静止画を結合",
        "thumb_mode": "選択モード",
        "mode_extract": "動画から抽出",
        "mode_upload": "画像をアップロード",
        "btn_extract_thumb": "📸 この瞬間をサムネイルにする",
        "thumb_done": "✅ サムネイル確定済み",
        "btn_convert_anim": "🚀 アニメーション変換を開始",
        # 静止画抽出用
        "image_title": "📷 静止画抽出設定",
        "extract_settings": "⚙️ 抽出・出力設定",
        "extract_mode": "抽出方法",
        "mode_count": "指定枚数で均等抽出",
        "mode_interval": "一定間隔(秒)で抽出",
        "extract_count": "抽出枚数",
        "extract_interval": "間隔(秒)",
        "image_format": "画像形式",
        "jpeg_quality": "JPEG品質 (低← →高)",
        "btn_extract_image": "🚀 静止画抽出を開始 (ZIP作成)",
        # ステータスメッセージ
        "status_cut": "動画をカット中...",
        "status_resize": "リサイズ中...",
        "status_wm": "透かしを合成中...",
        "status_thumb": "サムネイルを結合中...",
        "status_export_anim": "アニメーション変換中...（時間がかかります）",
        "status_extracting": "画像を抽出・加工中...",
        "status_zipping": "ZIPファイルを作成中...",
        "finish": "✨ 完了しました！",
        "download_anim": "📥 アニメーションを保存",
        "download_zip": "📥 画像ZIPを保存",
        "info_upload": "まずは動画ファイルをアップロードしてください。",
        "err_count": "枚数は2枚以上を指定してください。",
        "err_interval": "間隔は0秒より大きくしてください。"
    },
    "English": {
        "title": "V-Convert Pro (Multi-Media Converter)",
        # Sidebar
        "mode_select": "Select Mode",
        "mode_anim": "🎬 Animation Convert (GIF/WebP)",
        "mode_image": "📷 Frame Extraction (PNG/JPG)",
        "guide": "📖 User Guide",
        "guide_anim": """
        **[Animation Mode]**
        1. Upload video.
        2. Set trim range if needed.
        3. Set output format and size.
        4. Configure watermarks (max 3).
        5. Confirm thumbnail if using one.
        6. Click "Start Conversion".
        """,
        "guide_image": """
        **[Frame Extraction Mode]**
        1. Upload video.
        2. Select extraction mode (By count or interval).
        3. Set output format (JPEG recommended) and quality.
        4. Configure watermarks (applied to all images).
        5. Click "Start Extraction".
        6. Download the ZIP file.
        """,
        # Common
        "upload_label": "Select Video File",
        "video_info": "Video Info",
        "duration": "Duration",
        "resolution": "Original Res",
        "wm_section": "✒️ Watermark Settings (Max 3)",
        "wm_enable": "Enable",
        "wm_text": "Text",
        "wm_pos": "Position",
        "wm_color": "Color",
        "wm_size": "Size",
        "wm_opacity": "Opacity",
        "wm_shadow": "Outline",
        "font_src": "Font",
        "font_list": "List",
        "font_upload": "Upload",
        "pos_opts": ["Bottom Right", "Bottom Left", "Top Left", "Top Right", "Center"],
        # Animation
        "anim_title": "🎬 Animation Settings",
        "cut_section": "✂️ Trim Video",
        "start_time": "Start Time (sec)",
        "end_time": "End Time (sec)",
        "basic_settings": "⚙️ Basic Settings",
        "output_format": "Output Format",
        "resize_width": "Resize Width (px)",
        "fps": "FPS",
        "thumb_section": "🖼 Thumbnail Settings",
        "thumb_enable": "Add static frame at start",
        "thumb_mode": "Mode",
        "mode_extract": "Extract from video",
        "mode_upload": "Upload image",
        "btn_extract_thumb": "📸 Set as thumbnail",
        "thumb_done": "✅ Thumbnail confirmed",
        "btn_convert_anim": "🚀 Start Animation Conversion",
        # Image Extraction
        "image_title": "📷 Frame Extraction Settings",
        "extract_settings": "⚙️ Extraction & Output Settings",
        "extract_mode": "Extraction Method",
        "mode_count": "Total Count (Evenly spaced)",
        "mode_interval": "Time Interval (sec)",
        "extract_count": "Total Images",
        "extract_interval": "Interval (sec)",
        "image_format": "Image Format",
        "jpeg_quality": "JPEG Quality (Low← →High)",
        "btn_extract_image": "🚀 Start Extraction (Create ZIP)",
        # Status
        "status_cut": "Trimming video...",
        "status_resize": "Resizing...",
        "status_wm": "Applying watermarks...",
        "status_thumb": "Merging thumbnail...",
        "status_export_anim": "Converting animation... (Takes time)",
        "status_extracting": "Extracting and processing frames...",
        "status_zipping": "Creating ZIP file...",
        "finish": "✨ Completed!",
        "download_anim": "📥 Download Animation",
        "download_zip": "📥 Download ZIP",
        "info_upload": "Please upload a video file first.",
        "err_count": "Count must be 2 or more.",
        "err_interval": "Interval must be greater than 0 seconds."
    }
}

# --- ページ設定 ---
st.set_page_config(page_title="V-Convert Pro", layout="wide", page_icon="🎥")

# --- サイドバー (言語とモード選択) ---
selected_lang = st.sidebar.selectbox("Language / 言語", ["日本語", "English"])
L = LANGUAGES[selected_lang]

st.sidebar.divider()
# 機能モード選択
app_mode = st.sidebar.radio(L["mode_select"], [L["mode_anim"], L["mode_image"]])

st.sidebar.divider()
st.sidebar.title(L["guide"])
# モードに応じてガイドを切り替え
if app_mode == L["mode_anim"]:
    st.sidebar.info(L["guide_anim"])
else:
    st.sidebar.info(L["guide_image"])

# --- フォント準備 ---
FONTS_DIR = "fonts"
available_fonts = sorted([f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))]) if os.path.exists(FONTS_DIR) else []

# --- 透かし描画関数 (共通) ---
def draw_watermarks(pil_img, wm_configs):
    img = pil_img.convert("RGBA")
    W, H = img.size
    for wm in wm_configs:
        txt_layer = Image.new("RGBA", img.size, (255,255,255,0))
        d = ImageDraw.Draw(txt_layer)
        try: fnt = ImageFont.truetype(wm["font"], wm["size"]) if wm["font"] else ImageFont.load_default()
        except: fnt = ImageFont.load_default()
        
        b = d.textbbox((0,0), wm["text"], font=fnt)
        tw, th, m = b[2]-b[0], b[3]-b[1], 20
        
        pos_idx = L["pos_opts"].index(wm["pos"])
        if pos_idx == 0: x, y = W-tw-m, H-th-m # 右下
        elif pos_idx == 1: x, y = m, H-th-m # 左下
        elif pos_idx == 2: x, y = m, m # 左上
        elif pos_idx == 3: x, y = W-tw-m, m # 右上
        else: x, y = (W-tw)/2, (H-th)/2 # 中央
        
        rgb, fill = ImageColor.getrgb(wm["color"]), (0,0,0,int(255*wm["opacity"]/100))
        if wm["shadow"]:
            for ax in range(-2,3):
                for ay in range(-2,3): d.text((x+ax, y+ay), wm["text"], font=fnt, fill=fill)
        d.text((x,y), wm["text"], font=fnt, fill=(rgb[0],rgb[1],rgb[2],int(255*wm["opacity"]/100)))
        img = Image.alpha_composite(img, txt_layer)
    return img.convert("RGB")


# --- メイン画面 ---
st.title(L["title"])

uploaded_file = st.file_uploader(L["upload_label"], type=['mp4', 'mov', 'avi'])

if uploaded_file is not None:
    # 動画の一時保存
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(uploaded_file.read())
    video_path = tfile.name
    
    if 'last_video_name' not in st.session_state or st.session_state.last_video_name != uploaded_file.name:
        st.session_state.last_video_name = uploaded_file.name
        st.session_state.selected_thumb_img = None
    
    try:
        clip = VideoFileClip(video_path)
        col_pre1, col_pre2 = st.columns([2, 1])
        with col_pre1: st.video(video_path)
        with col_pre2:
            st.subheader(L["video_info"])
            st.metric(L["duration"], f"{clip.duration:.1f} s")
            st.metric(L["resolution"], f"{clip.w} x {clip.h}")
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

    # ==========================================
    # モードA: アニメーション変換 (GIF/WebP)
    # ==========================================
    if app_mode == L["mode_anim"]:
        st.header(L["anim_title"])

        with st.expander(L["cut_section"]):
            c_cut1, c_cut2 = st.columns(2)
            start_t = c_cut1.number_input(L["start_time"], 0.0, clip.duration, 0.0, 0.1)
            end_t = c_cut2.number_input(L["end_time"], 0.0, clip.duration, clip.duration, 0.1)

        with st.expander(L["basic_settings"]):
            c1, c2, c3 = st.columns(3)
            out_fmt = c1.selectbox(L["output_format"], ["GIF", "WebP"])
            resize_width = c2.number_input(L["resize_width"], 100, 2000, 300)
            fps = c3.slider(L["fps"], 1, 60, 10)

        with st.expander(L["wm_section"]):
            wm_configs = []
            tabs = st.tabs([f"WM {i+1}" for i in range(3)])
            for i, tab in enumerate(tabs):
                with tab:
                    if st.checkbox(L["wm_enable"], key=f"a_en_{i}"):
                        txt = st.text_input(L["wm_text"], f"Text {i+1}", key=f"a_txt_{i}")
                        c_wm1, c_wm2, c_wm3 = st.columns(3)
                        with c_wm1:
                            pos = st.selectbox(L["wm_pos"], L["pos_opts"], key=f"a_pos_{i}")
                            color = st.color_picker(L["wm_color"], "#FFFFFF", key=f"a_col_{i}")
                        with c_wm2:
                            size = st.slider(L["wm_size"], 10, 200, 40, key=f"a_size_{i}")
                            opacity = st.slider(L["wm_opacity"], 0, 100, 100, key=f"a_op_{i}")
                        with c_wm3:
                            shadow = st.checkbox(L["wm_shadow"], value=True, key=f"a_shd_{i}")
                            fnt_src = st.radio(L["font_src"], [L["font_list"], L["font_upload"]], horizontal=True, key=f"a_fsrc_{i}")
                        
                        f_path = None
                        if fnt_src == L["font_list"]:
                            if available_fonts: f_path = os.path.join(FONTS_DIR, st.selectbox(f"{L['font_src']} select", available_fonts, key=f"a_fsel_{i}"))
                        else:
                            f_file = st.file_uploader("Font file", type=["ttf", "otf"], key=f"a_fup_{i}")
                            if f_file:
                                f_path = f"temp_a_f_{i}.ttf"
                                with open(f_path, "wb") as f: f.write(f_file.read())
                        wm_configs.append({"text": txt, "pos": pos, "color": color, "size": size, "opacity": opacity, "shadow": shadow, "font": f_path})

        with st.expander(L["thumb_section"]):
            enable_thumb = st.checkbox(L["thumb_enable"])
            thumb_img_final = None
            if enable_thumb:
                t_mode = st.radio(L["thumb_mode"], [L["mode_extract"], L["mode_upload"]], horizontal=True)
                if t_mode == L["mode_extract"]:
                    t_time = st.slider("sec", 0.0, max(0.0, clip.duration-0.1), 0.0, 0.1)
                    if st.button(L["btn_extract_thumb"]):
                        st.session_state.selected_thumb_img = Image.fromarray(clip.get_frame(t_time))
                        st.rerun()
                    if st.session_state.selected_thumb_img:
                        st.image(st.session_state.selected_thumb_img, width=200)
                        st.success(L["thumb_done"])
                        thumb_img_final = st.session_state.selected_thumb_img
                else:
                    f_thumb = st.file_uploader("Image", type=["png", "jpg"])
                    if f_thumb: thumb_img_final = Image.open(f_thumb)

        st.markdown("---")
        if st.button(L["btn_convert_anim"], type="primary"):
            prog = st.progress(0); status = st.empty()
            try:
                status.text(L["status_cut"]); processed = clip.subclip(start_t, end_t); prog.progress(10)
                status.text(L["status_resize"]); processed = processed.resize(width=resize_width); prog.progress(30)
                if wm_configs:
                    status.text(L["status_wm"])
                    processed = processed.fl_image(lambda frame: np.array(draw_watermarks(Image.fromarray(frame), wm_configs)))
                prog.progress(50)
                if enable_thumb and thumb_img_final:
                    status.text(L["status_thumb"]); t_img = thumb_img_final.convert("RGB")
                    th_h = int(resize_width * (t_img.height / t_img.width)); t_img = t_img.resize((resize_width, th_h), Image.Resampling.LANCZOS)
                    t_clip = ImageClip(np.array(t_img)).set_duration(0.1).set_fps(fps)
                    processed = concatenate_videoclips([t_clip, processed], method="compose")
                prog.progress(70)
                status.text(L["status_export_anim"]); out_name = f"output.{out_fmt.lower()}"
                if out_fmt == "WebP": processed.write_videofile(out_name, fps=fps, codec='libwebp', ffmpeg_params=["-preset", "default", "-loop", "0", "-qscale", "80", "-method", "0"])
                else: processed.write_gif(out_name, fps=fps)
                prog.progress(100); status.success(L["finish"])
                with open(out_name, "rb") as f: st.download_button(L["download_anim"], f, file_name=f"result.{out_fmt.lower()}")
                st.image(out_name)
            except Exception as e: st.error(f"Error: {e}")
            finally: clip.close(); (processed.close() if 'processed' in locals() else None)

    # ==========================================
    # モードB: 静止画抽出 (PNG/JPG) - 新機能
    # ==========================================
    else:
        st.header(L["image_title"])

        with st.expander(L["extract_settings"], expanded=True):
            c_ex1, c_ex2 = st.columns(2)
            with c_ex1:
                extract_method = st.radio(L["extract_mode"], [L["mode_count"], L["mode_interval"]])
            with c_ex2:
                if extract_method == L["mode_count"]:
                    extract_count = st.number_input(L["extract_count"], min_value=2, value=10, step=1)
                else:
                    extract_interval = st.number_input(L["extract_interval"], min_value=0.1, value=1.0, step=0.1)
            
            c_set1, c_set2, c_set3 = st.columns(3)
            resize_width_img = c_set1.number_input(L["resize_width"], 100, 4000, 1920)
            img_format = c_set2.selectbox(L["image_format"], ["JPEG", "PNG"])
            jpeg_quality = c_set3.slider(L["jpeg_quality"], 10, 100, 85) if img_format == "JPEG" else 100

        # 透かし設定 (アニメーション用とコードは同じだがキーを変えて独立させる)
        with st.expander(L["wm_section"]):
            wm_configs_img = []
            tabs_img = st.tabs([f"WM {i+1}" for i in range(3)])
            for i, tab in enumerate(tabs_img):
                with tab:
                    if st.checkbox(L["wm_enable"], key=f"i_en_{i}"):
                        txt = st.text_input(L["wm_text"], f"Text {i+1}", key=f"i_txt_{i}")
                        c_wm1, c_wm2, c_wm3 = st.columns(3)
                        with c_wm1:
                            pos = st.selectbox(L["wm_pos"], L["pos_opts"], key=f"i_pos_{i}")
                            color = st.color_picker(L["wm_color"], "#FFFFFF", key=f"i_col_{i}")
                        with c_wm2:
                            size = st.slider(L["wm_size"], 10, 200, 40, key=f"i_size_{i}")
                            opacity = st.slider(L["wm_opacity"], 0, 100, 100, key=f"i_op_{i}")
                        with c_wm3:
                            shadow = st.checkbox(L["wm_shadow"], value=True, key=f"i_shd_{i}")
                            fnt_src = st.radio(L["font_src"], [L["font_list"], L["font_upload"]], horizontal=True, key=f"i_fsrc_{i}")
                        
                        f_path = None
                        if fnt_src == L["font_list"]:
                            if available_fonts: f_path = os.path.join(FONTS_DIR, st.selectbox(f"{L['font_src']} select", available_fonts, key=f"i_fsel_{i}"))
                        else:
                            f_file = st.file_uploader("Font file", type=["ttf", "otf"], key=f"i_fup_{i}")
                            if f_file:
                                f_path = f"temp_i_f_{i}.ttf"
                                with open(f_path, "wb") as f: f.write(f_file.read())
                        wm_configs_img.append({"text": txt, "pos": pos, "color": color, "size": size, "opacity": opacity, "shadow": shadow, "font": f_path})

        st.markdown("---")
        if st.button(L["btn_extract_image"], type="primary"):
            # 入力チェック
            if extract_method == L["mode_count"] and extract_count < 2: st.error(L["err_count"]); st.stop()
            if extract_method == L["mode_interval"] and extract_interval <= 0: st.error(L["err_interval"]); st.stop()

            prog = st.progress(0); status = st.empty()
            status.text(L["status_extracting"])
            
            try:
                # 抽出する時間のリストを作成
                if extract_method == L["mode_count"]:
                    times = np.linspace(0, clip.duration - 0.1, extract_count)
                else:
                    times = np.arange(0, clip.duration - 0.1, extract_interval)
                
                total_frames = len(times)
                if total_frames == 0: st.error("抽出対象のフレームがありません。"); st.stop()

                # 一時ディレクトリ作成
                tmp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(tempfile.gettempdir(), "images.zip")

                # ループ処理
                for i, t in enumerate(times):
                    # フレーム取得 -> PIL変換
                    frame = clip.get_frame(t)
                    img = Image.fromarray(frame)
                    
                    # リサイズ
                    aspect = img.height / img.width
                    target_h = int(resize_width_img * aspect)
                    img = img.resize((resize_width_img, target_h), Image.Resampling.LANCZOS)
                    
                    # 透かし合成
                    if wm_configs_img:
                        img = draw_watermarks(img, wm_configs_img)
                    
                    # 保存
                    ext = "jpg" if img_format == "JPEG" else "png"
                    save_path = os.path.join(tmp_dir, f"image_{i+1:03d}.{ext}")
                    if img_format == "JPEG":
                        img.convert("RGB").save(save_path, quality=jpeg_quality)
                    else:
                        img.save(save_path)
                    
                    prog.progress(int((i + 1) / total_frames * 80)) # 80%まで進める

                # ZIP作成
                status.text(L["status_zipping"])
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for root, dirs, files in os.walk(tmp_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), file)
                
                prog.progress(100)
                status.success(L["finish"])
                
                # ダウンロードボタン
                with open(zip_path, "rb") as f:
                    st.download_button(L["download_zip"], f, file_name="extracted_images.zip", mime="application/zip")

            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                clip.close()
                # お掃除
                if 'tmp_dir' in locals() and os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
                if 'zip_path' in locals() and os.path.exists(zip_path): os.remove(zip_path)

else:
    st.info(L["info_upload"])
