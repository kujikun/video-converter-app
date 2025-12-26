import streamlit as st
import tempfile
import os
from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageFont, ImageDraw, ImageColor
import numpy as np

# --- 言語設定辞書 ---
LANGUAGES = {
    "日本語": {
        "title": "V-Convert Pro (多言語版)",
        "guide": "📖 使い方ガイド",
        "guide_text": "1. 動画をアップ\n2. カット範囲を指定\n3. 設定（形式・サイズ）\n4. 透かし（最大3つ）\n5. サムネ確定\n6. 変換開始",
        "upload_label": "動画ファイルを選択",
        "video_info": "動画情報",
        "duration": "長さ",
        "resolution": "元の解像度",
        "cut_section": "✂️ 動画のカット (トリミング)",
        "start_time": "開始時間 (秒)",
        "end_time": "終了時間 (秒)",
        "warning_time": "開始時間は終了時間より前に設定してください。",
        "basic_settings": "⚙️ 基本変換設定",
        "output_format": "出力形式",
        "resize_width": "横幅リサイズ (px)",
        "fps": "FPS (滑らかさ)",
        "watermark_section": "✒️ 透かし文字の設定 (最大3つ)",
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
        "thumb_section": "🖼 サムネイル(先頭フレーム)の設定",
        "thumb_enable": "先頭に静止画を結合",
        "thumb_mode": "選択モード",
        "mode_extract": "動画から抽出",
        "mode_upload": "画像をアップロード",
        "btn_extract": "📸 この瞬間をサムネイルにする",
        "thumb_done": "✅ サムネイル確定済み",
        "thumb_warn": "画像が確定していません。ボタンを押してください。",
        "btn_convert": "🚀 変換を開始する",
        "status_cut": "動画をカット中...",
        "status_resize": "リサイズ中...",
        "status_wm": "透かしを合成中...",
        "status_thumb": "サムネイルを結合中...",
        "status_export": "変換中...（時間がかかります）",
        "finish": "✨ 完了しました！",
        "download": "📥 保存する",
        "info_upload": "まずは動画ファイルをアップロードしてください。"
    },
    "English": {
        "title": "V-Convert Pro (Multi-Language)",
        "guide": "📖 User Guide",
        "guide_text": "1. Upload video\n2. Set cut range\n3. Set format/size\n4. Set watermarks (max 3)\n5. Confirm thumbnail\n6. Start conversion",
        "upload_label": "Select Video File",
        "video_info": "Video Info",
        "duration": "Duration",
        "resolution": "Original Res",
        "cut_section": "✂️ Trim Video",
        "start_time": "Start Time (sec)",
        "end_time": "End Time (sec)",
        "warning_time": "Start time must be before end time.",
        "basic_settings": "⚙️ Basic Settings",
        "output_format": "Output Format",
        "resize_width": "Resize Width (px)",
        "fps": "FPS",
        "watermark_section": "✒️ Watermark Settings (Max 3)",
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
        "thumb_section": "🖼 Thumbnail Settings",
        "thumb_enable": "Add static frame at start",
        "thumb_mode": "Mode",
        "mode_extract": "Extract from video",
        "mode_upload": "Upload image",
        "btn_extract": "📸 Set this frame as thumbnail",
        "thumb_done": "✅ Thumbnail confirmed",
        "thumb_warn": "Thumbnail not confirmed. Click the button.",
        "btn_convert": "🚀 Start Conversion",
        "status_cut": "Trimming video...",
        "status_resize": "Resizing...",
        "status_wm": "Applying watermarks...",
        "status_thumb": "Merging thumbnail...",
        "status_export": "Converting... (This may take a while)",
        "finish": "✨ Completed!",
        "download": "📥 Download",
        "info_upload": "Please upload a video file first."
    }
}

# --- ページ設定 ---
st.set_page_config(page_title="V-Convert Pro", layout="wide", page_icon="🎥")

# --- 言語選択サイドバー ---
selected_lang = st.sidebar.selectbox("Language / 言語", ["日本語", "English"])
L = LANGUAGES[selected_lang]

with st.sidebar:
    st.title(L["guide"])
    st.info(L["guide_text"])

# --- フォント準備 ---
FONTS_DIR = "fonts"
available_fonts = sorted([f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))]) if os.path.exists(FONTS_DIR) else []

# --- メイン画面 ---
st.title(L["title"])

uploaded_file = st.file_uploader(L["upload_label"], type=['mp4', 'mov', 'avi'])

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
            st.subheader(L["video_info"])
            st.metric(L["duration"], f"{clip.duration:.1f} s")
            st.metric(L["resolution"], f"{clip.w} x {clip.h}")
            
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

    # --- 各種設定 ---
    with st.expander(L["cut_section"]):
        c_cut1, c_cut2 = st.columns(2)
        start_t = c_cut1.number_input(L["start_time"], 0.0, clip.duration, 0.0, 0.1)
        end_t = c_cut2.number_input(L["end_time"], 0.0, clip.duration, clip.duration, 0.1)
        if start_t >= end_t: st.warning(L["warning_time"])

    with st.expander(L["basic_settings"]):
        c1, c2, c3 = st.columns(3)
        out_fmt = c1.selectbox(L["output_format"], ["GIF", "WebP"])
        resize_width = c2.number_input(L["resize_width"], 100, 2000, 300)
        fps = c3.slider(L["fps"], 5, 30, 10)

    with st.expander(L["watermark_section"]):
        wm_configs = []
        tab_titles = [f"WM {i+1}" for i in range(3)]
        tabs = st.tabs(tab_titles)
        for i, tab in enumerate(tabs):
            with tab:
                enabled = st.checkbox(L["wm_enable"], key=f"en_{i}")
                if enabled:
                    txt = st.text_input(L["wm_text"], f"Text {i+1}", key=f"txt_{i}")
                    c_wm1, c_wm2, c_wm3 = st.columns(3)
                    with c_wm1:
                        pos = st.selectbox(L["wm_pos"], ["右下", "左下", "左上", "右上", "中央"], key=f"pos_{i}")
                        color = st.color_picker(L["wm_color"], "#FFFFFF", key=f"col_{i}")
                    with c_wm2:
                        size = st.slider(L["wm_size"], 10, 200, 40, key=f"size_{i}")
                        opacity = st.slider(L["wm_opacity"], 0, 100, 100, key=f"op_{i}")
                    with c_wm3:
                        shadow = st.checkbox(L["wm_shadow"], value=True, key=f"shd_{i}")
                        fnt_src = st.radio(L["font_src"], [L["font_list"], L["font_upload"]], horizontal=True, key=f"fsrc_{i}")
                    
                    f_path = None
                    if fnt_src == L["font_list"]:
                        if available_fonts:
                            f_path = os.path.join(FONTS_DIR, st.selectbox(f"{L['font_src']} select", available_fonts, key=f"fsel_{i}"))
                    else:
                        f_file = st.file_uploader("Font file", type=["ttf", "otf"], key=f"fup_{i}")
                        if f_file:
                            f_path = f"temp_f_{i}.ttf"
                            with open(f_path, "wb") as f: f.write(f_file.read())
                    
                    wm_configs.append({"text": txt, "pos": pos, "color": color, "size": size, "opacity": opacity, "shadow": shadow, "font": f_path})

    with st.expander(L["thumb_section"]):
        enable_thumb = st.checkbox(L["thumb_enable"])
        thumb_img_final = None
        if enable_thumb:
            t_mode = st.radio(L["thumb_mode"], [L["mode_extract"], L["mode_upload"]], horizontal=True)
            if t_mode == L["mode_extract"]:
                t_time = st.slider("sec", 0.0, max(0.0, clip.duration-0.2), 0.0, 0.1)
                if st.button(L["btn_extract"]):
                    st.session_state.selected_thumb_img = Image.fromarray(clip.get_frame(t_time))
                    st.rerun()
                if st.session_state.selected_thumb_img:
                    st.image(st.session_state.selected_thumb_img, width=200)
                    st.success(L["thumb_done"])
                    thumb_img_final = st.session_state.selected_thumb_img
                else:
                    st.warning(L["thumb_warn"])
            else:
                f_thumb = st.file_uploader("Image", type=["png", "jpg"])
                if f_thumb: thumb_img_final = Image.open(f_thumb)

    # --- 実行セクション ---
    st.markdown("---")
    if st.button(L["btn_convert"], type="primary"):
        prog = st.progress(0)
        status = st.empty()
        try:
            status.text(L["status_cut"])
            processed = clip.subclip(start_t, end_t)
            prog.progress(10)
            
            status.text(L["status_resize"])
            processed = processed.resize(width=resize_width)
            prog.progress(30)
            
            if wm_configs:
                status.text(L["status_wm"])
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
                        rgb, fill = ImageColor.getrgb(wm["color"]), (0,0,0,int(255*wm["opacity"]/100))
                        if wm["shadow"]:
                            for ax in range(-2,3):
                                for ay in range(-2,3): d.text((x+ax, y+ay), wm["text"], font=fnt, fill=fill)
                        d.text((x,y), wm["text"], font=fnt, fill=(rgb[0],rgb[1],rgb[2],int(255*wm["opacity"]/100)))
                        img = Image.alpha_composite(img, txt_layer)
                    return np.array(img.convert("RGB"))
                processed = processed.fl_image(draw_all_wm)
            prog.progress(50)

            if enable_thumb and thumb_img_final:
                status.text(L["status_thumb"])
                t_img = thumb_img_final.convert("RGB")
                th_h = int(resize_width * (t_img.height / t_img.width))
                t_img = t_img.resize((resize_width, th_h), Image.Resampling.LANCZOS)
                t_clip = ImageClip(np.array(t_img)).set_duration(0.1).set_fps(fps)
                processed = concatenate_videoclips([t_clip, processed], method="compose")
            prog.progress(70)

            status.text(L["status_export"])
            out_name = f"output.{out_fmt.lower()}"
            if out_fmt == "WebP":
                processed.write_videofile(out_name, fps=fps, codec='libwebp', ffmpeg_params=["-preset", "default", "-loop", "0", "-qscale", "80", "-method", "0"])
            else:
                processed.write_gif(out_name, fps=fps)
            
            prog.progress(100)
            status.success(L["finish"])
            with open(out_name, "rb") as f:
                st.download_button(L["download"], f, file_name=f"result.{out_fmt.lower()}")
            st.image(out_name)
        except Exception as e: st.error(f"Error: {e}")
        finally:
            clip.close()
            if 'processed' in locals(): processed.close()
else:
    st.info(L["info_upload"])
