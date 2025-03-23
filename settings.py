COMPANY_MAPPING = {
        'reliance': 'Reliance Industries',
        'reliance industries': 'Reliance Industries',
        'tata-group': 'Tata Group',
        'tata group': 'Tata Group',
        'unilever': 'Unilever Global',
        'unilever global':'Unilever Global',
        'nestle-s-a-': 'Nestle Global',
        'nestlé global': 'Nestle Global',
        'aditya-birla-group': 'Aditya Birla Group',
        'aditya birla group': 'Aditya Birla Group',
        'maricolimited': 'Marico',
        'marico': 'Marico',
        'hul': 'HUL',
        'mahindragroup': 'Mahindra & Mahindra',
        'mahindra & mahindra': 'Mahindra & Mahindra',
        'itc-limited': 'ITC Limited',
        'https://www.loreal.com/en/india/': 'ITC Limited',
        'mondelezinternational': 'Mondelez International',
        'mondelez international': 'Mondelez International'
}
YOUTUBE_MAPPING={
  "Mahindra & Mahindra": "MahindraRise",
  "Marico": "Marico",
  "Mondelez International": "Mondelez International",
  "Reliance Industries": "RelianceUpdates",
  "Tata Group": "TataCompanies",
  "Unilever Global": "Unilever Global",
  'Aditya Birla Group': 'aditya-birla-group',
  'Aditya Birla Group': 'aditya birla group',
}


RIVAL_IQ = [
                "published_at", "report_generated_at", "captured_at", "company", "channel",
                "presence_handle", "message", "post_link", "link", "link_title", 
                "link_description", "image", "post_type", "posted_domain", "posted_url", 
                "engagement_total", "applause", "conversation", "amplification", "audience", 
                "engagement_rate_by_follower", "engagement_rate_lift", "post_tag_ugc", 
                "post_tag_contests","video_views"
            ]

PHANTOM_BUSTER = [
                "postUrl", "imgUrl", "type", "postContent", "likeCount",
                "commentCount", "repostCount", "postDate", "action",
                "profileUrl", "timestamp", "postTimestamp", "videoUrl",
                "sharedPostUrl"
            ]







#####################DATABASE######################


CONNECTION_URL="mongodb+srv://lalsharath511:Sharathbhagavan15192142@legal.mosm3f4.mongodb.net/"
DATABASE_NAME="echo2"
COLLECTION_POST="posts"
COLLECTION_UPLOAD="uploaded_data"
COLLECTION_KEYWORD="keyword_data"
COLLECTION_DUPLICATE="duplicate_data"
COLLECTION_METADATA="metadata"
