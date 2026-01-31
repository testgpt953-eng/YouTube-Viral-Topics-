import streamlit as st
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# YouTube API Key 
API_KEY = "AIzaSyDHE3DYw9DKpBDvW1ijAs_IwCzCz6XKcNM"

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Language mapping (Display Name -> YouTube Language Code)
LANGUAGE_OPTIONS = {
    "🇺🇸 English": "en",
    "🇪🇸 Spanish (Español)": "es",
    "🇫🇷 French (Français)": "fr",
    "🇩🇪 German (Deutsch)": "de",
    "🇵🇹 Portuguese (Português)": "pt",
    "🇮🇹 Italian (Italiano)": "it",
    "🇯🇵 Japanese (日本語)": "ja",
    "🇰🇷 Korean (한국어)": "ko",
    "🇮🇳 Hindi (हिन्दी)": "hi",
    "🇨🇳 Chinese (中文)": "zh"
}

# Function to generate relevant keywords from niche
def generate_keywords_from_niche(niche):
    """
    Generate search keywords based on niche category
    """
    base_keywords = [niche]
    
    # Add common viral modifiers
    modifiers = [
        f"{niche} tutorial",
        f"{niche} tips",
        f"{niche} guide",
        f"{niche} how to",
        f"best {niche}",
        f"{niche} explained",
        f"{niche} beginner",
        f"{niche} mistakes",
        f"{niche} secrets",
        f"{niche} hacks"
    ]
    
    return base_keywords + modifiers

# Streamlit App Title
st.title("🔥 YouTube Niche Analyzer & Trending Finder")
st.markdown("Automatically discover top channels and trending titles in any niche!")

# ========== INPUT PARAMETERS ==========
st.header("📊 Input Parameters")

col1, col2 = st.columns(2)

with col1:
    # 1) Niche/Category Name
    niche_name = st.text_input(
        "1️⃣ Enter Niche/Category Name:",
        value="",
        placeholder="e.g., AI tools, fitness, cooking, gaming"
    )
    
    # 2) Max Subscribers
    subscriber_limit = st.number_input(
        "2️⃣ Max Subscriber Count:",
        min_value=0,
        max_value=1000000,
        value=5000,
        step=1000,
        help="Channels with fewer subscribers than this will be included"
    )
    
    # 3) Days to search
    days = st.number_input(
        "3️⃣ Search Last X Days:",
        min_value=1,
        max_value=30,
        value=7
    )

with col2:
    # 4) Number of top channels
    num_top_channels = st.number_input(
        "4️⃣ Number of Top Channels Needed:",
        min_value=1,
        max_value=20,
        value=5
    )
    
    # 5) Number of titles needed
    num_titles = st.number_input(
        "5️⃣ Number of Trending Titles Needed:",
        min_value=1,
        max_value=50,
        value=10
    )
    
    # 6) Language Selection (NEW!)
    selected_language_display = st.selectbox(
        "6️⃣ Select Language:",
        options=list(LANGUAGE_OPTIONS.keys()),
        index=0,  # Default to English
        help="Filter videos by language"
    )

# Get the language code for API
selected_language_code = LANGUAGE_OPTIONS[selected_language_display]

# Advanced options (collapsible)
with st.expander("⚙️ Advanced Options"):
    search_depth = st.slider(
        "Search Depth (more = better accuracy but slower):",
        min_value=10,
        max_value=50,
        value=30,
        help="Number of videos to analyze per keyword"
    )

# ========== FETCH DATA BUTTON ==========
if st.button("🚀 Analyze Niche", type="primary"):
    
    # Validation
    if not niche_name or not niche_name.strip():
        st.error("❌ Please enter a niche/category name!")
    else:
        try:
            with st.spinner(f"🔍 Analyzing '{niche_name}' niche in {selected_language_display}..."):
                
                # Generate keywords automatically
                keywords = generate_keywords_from_niche(niche_name.strip())
                
                st.info(f"🎯 Generated {len(keywords)} search keywords from niche: {niche_name}")
                st.info(f"🌍 Searching in language: {selected_language_display}")
                with st.expander("View Generated Keywords"):
                    st.write(", ".join(keywords))
                
                # Calculate date range
                start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
                
                # Storage for results
                all_videos = []
                channel_data_map = {}  # channel_id -> {name, subs, total_views, video_count}
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Search for each keyword
                for idx, keyword in enumerate(keywords):
                    status_text.text(f"Searching: {keyword} ({idx+1}/{len(keywords)})")
                    progress_bar.progress((idx + 1) / len(keywords))
                    
                    # Search parameters (WITH LANGUAGE FILTER)
                    search_params = {
                        "part": "snippet",
                        "q": keyword,
                        "type": "video",
                        "order": "viewCount",
                        "publishedAfter": start_date,
                        "maxResults": search_depth,
                        "relevanceLanguage": selected_language_code,  # ✅ LANGUAGE FILTER
                        "key": API_KEY,
                    }
                    
                    # Fetch video data
                    response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
                    data = response.json()
                    
                    if "items" not in data or not data["items"]:
                        continue
                    
                    videos = data["items"]
                    
                    video_ids = [
                        video["id"]["videoId"]
                        for video in videos
                        if "id" in video and "videoId" in video["id"]
                    ]
                    
                    if not video_ids:
                        continue
                    
                    # Fetch video statistics
                    stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
                    stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
                    stats_data = stats_response.json()
                    
                    if "items" not in stats_data:
                        continue
                    
                    video_stats_map = {
                        item["id"]: item["statistics"]
                        for item in stats_data["items"]
                    }
                    
                    # Get unique channel IDs
                    channel_ids = list(set([
                        video["snippet"]["channelId"]
                        for video in videos
                        if "snippet" in video and "channelId" in video["snippet"]
                    ]))
                    
                    # Fetch channel statistics (including channel name)
                    channel_params = {
                        "part": "statistics,snippet",  # Added snippet to get channel name
                        "id": ",".join(channel_ids),
                        "key": API_KEY
                    }
                    channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
                    channel_data = channel_response.json()
                    
                    if "items" not in channel_data:
                        continue
                    
                    # Build channel lookup with name
                    for channel in channel_data["items"]:
                        channel_id = channel["id"]
                        channel_name = channel["snippet"].get("title", "Unknown Channel")
                        subs = int(channel["statistics"].get("subscriberCount", 0))
                        
                        if channel_id not in channel_data_map:
                            channel_data_map[channel_id] = {
                                "name": channel_name,
                                "subs": subs,
                                "total_views": 0,
                                "video_count": 0,
                                "url": f"https://www.youtube.com/channel/{channel_id}"
                            }
                    
                    # Process videos
                    for video in videos:
                        video_id = video["id"]["videoId"]
                        channel_id = video["snippet"]["channelId"]
                        
                        if channel_id not in channel_data_map:
                            continue
                        
                        subs = channel_data_map[channel_id]["subs"]
                        
                        # Filter by subscriber count
                        if subs >= int(subscriber_limit):
                            continue
                        
                        title = video["snippet"].get("title", "N/A")
                        channel_name = video["snippet"].get("channelTitle", "Unknown")
                        description = video["snippet"].get("description", "")[:150]
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        thumbnail = video["snippet"]["thumbnails"].get("high", {}).get("url", "")
                        
                        views = int(video_stats_map.get(video_id, {}).get("viewCount", 0))
                        likes = int(video_stats_map.get(video_id, {}).get("likeCount", 0))
                        
                        # Update channel aggregate data
                        channel_data_map[channel_id]["total_views"] += views
                        channel_data_map[channel_id]["video_count"] += 1
                        
                        all_videos.append({
                            "title": title,
                            "description": description,
                            "url": video_url,
                            "thumbnail": thumbnail,
                            "views": views,
                            "likes": likes,
                            "channel_name": channel_name,
                            "channel_id": channel_id,
                            "subs": subs,
                        })
                
                progress_bar.empty()
                status_text.empty()
                
                # ========== PROCESS RESULTS ==========
                
                if not all_videos:
                    st.warning(f"❌ No videos found in '{niche_name}' niche with fewer than {subscriber_limit:,} subscribers in {selected_language_display}.")
                else:
                    st.success(f"✅ Found {len(all_videos)} videos from {len(channel_data_map)} channels in {selected_language_display}!")
                    
                    # ========== OUTPUT 1: TOP CHANNELS ==========
                    st.header("🏆 Top Trending Channels in This Niche")
                    
                    # Sort channels by total views
                    top_channels = sorted(
                        channel_data_map.items(),
                        key=lambda x: x[1]["total_views"],
                        reverse=True
                    )[:int(num_top_channels)]
                    
                    for rank, (channel_id, channel_info) in enumerate(top_channels, 1):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"### {rank}. [{channel_info['name']}]({channel_info['url']})")
                            st.markdown(
                                f"**📊 Subscribers:** {channel_info['subs']:,} | "
                                f"**👁️ Total Views (last {days} days):** {channel_info['total_views']:,} | "
                                f"**🎬 Videos Found:** {channel_info['video_count']}"
                            )
                        
                        with col2:
                            avg_views = channel_info['total_views'] // channel_info['video_count'] if channel_info['video_count'] > 0 else 0
                            st.metric("Avg Views/Video", f"{avg_views:,}")
                        
                        st.write("---")
                    
                    # ========== OUTPUT 2: TOP TRENDING TITLES ==========
                    st.header("🔥 Top Trending Video Titles")
                    
                    # Sort videos by views
                    top_videos = sorted(all_videos, key=lambda x: x["views"], reverse=True)[:int(num_titles)]
                    
                    for rank, video in enumerate(top_videos, 1):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            if video["thumbnail"]:
                                st.image(video["thumbnail"], width=200)
                        
                        with col2:
                            st.markdown(f"### #{rank}")
                            st.metric("Views", f"{video['views']:,}")
                            st.metric("Likes", f"{video['likes']:,}")
                        
                        st.markdown(f"### [{video['title']}]({video['url']})")
                        st.markdown(f"**📺 Channel:** {video['channel_name']} ({video['subs']:,} subs)")
                        st.markdown(f"**📝 Description:** {video['description']}...")
                        
                        st.write("---")
                    
                    # ========== DOWNLOAD OPTION ==========
                    st.header("💾 Export Data")
                    
                    # Prepare CSV data
                    csv_data = "Rank,Title,Channel,Subscribers,Views,Likes,URL\n"
                    for rank, video in enumerate(top_videos, 1):
                        csv_data += f"{rank},\"{video['title']}\",{video['channel_name']},{video['subs']},{video['views']},{video['likes']},{video['url']}\n"
                    
                    st.download_button(
                        label="📥 Download Trending Titles as CSV",
                        data=csv_data,
                        file_name=f"{niche_name}_{selected_language_code}_trending_titles.csv",
                        mime="text/csv"
                    )
        
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
            st.exception(e)
