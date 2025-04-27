from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import os
from django.core.files.storage import FileSystemStorage
import numpy as np
import matplotlib.pyplot as plt
import io
from django.http import JsonResponse
import base64
from .models import OnionSite
import requests
import json
from bs4 import BeautifulSoup
import re
import spacy
from nltk.corpus import stopwords
from collections import Counter
import pandas as pd

global crawl_links, text_data
nlp = spacy.load("en_core_web_sm")  # Load a small English model
stop_words = set(stopwords.words('english'))

proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

# Search Engines for .onion Links
SEARCH_ENGINES = [
    {
        'name': 'Ahmia',
        'html_url': "https://ahmia.fi/search/?q={}"
    },
    {
        'name': 'Onion.Live',
        'html_url': "https://onion.live/search?q={}"
    },
    {
        'name': 'Torch',
        'html_url': "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion/cgi-bin/omega/omega?q={}",
        'requires_tor': True
    }
]
from django.shortcuts import render, get_object_or_404
def view_onion_data(request):
    onion_sites = OnionSite.objects.all()  # Fetch all stored .onion URLs
    print("Retrieved Onion Data:", onion_sites)  # Debugging Line
    return render(request, "onion_details.html", {"onion_sites": onion_sites})


from django.shortcuts import render, get_object_or_404

def onion_detail(request, onion_id):
    onion_site = get_object_or_404(OnionSite, id=onion_id)

    return render(request, "onion_detail.html", {"onion_site": onion_site})
def recursiveUrl(url, link, depth):
    if depth == 5:
        return url
    else:
        try:
            page = requests.get(url + link.get('href'), proxies=proxies)
            soup = BeautifulSoup(page.text, 'html.parser')
            newlink = soup.find('a')
            if len(newlink) == 0:
                return link
            else:
                return link, recursiveUrl(url, newlink, depth + 1)
        except:
            print("Unreachable Url")
            pass
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
def register(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return render(request, "register.html")

        User.objects.create_user(username=username, email=email, password=password1)
        messages.success(request, "Registration successful! You can now log in.")
        return redirect("UserLogin")

    return render(request, "register.html")

def getLinks(crawl_links):
    page = requests.get(crawl_links[0], proxies=proxies)
    soup = BeautifulSoup(page.text, 'html.parser')
    links = soup.find_all('a')
    for link in links:
        if len(crawl_links) < 7:
            link_name = recursiveUrl(crawl_links[0], link, 0)
            print(link_name)
            if link_name is not None:
                link_name = link_name[0]
                link_name = link_name.get('href')
                print(str(len(crawl_links))+" "+str(link_name))
                if "http://" in link_name or  "https://" in link_name:
                    crawl_links.append(link_name)
        else:
            break        
    return crawl_links

import datetime
from Crawler_frontend.models import OnionSite  # Ensure model is imported


import datetime
from django.db.utils import IntegrityError
from Crawler_frontend.models import OnionSite  # Ensure model is imported

from google import genai

# Configure Gemini API
GEMINI_API_KEY = ""  # Replace with your actual Gemini API Key

def format_text_with_gemini(text):
    """Use Gemini AI to structure and format the extracted dark web text."""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt = f"""
        The following text is extracted from a dark web website. 
        Please structure it in a clean, readable format with proper headings, bullet points, and spacing.

        Extracted Text:
        {text}

        Return only the structured and formatted text.
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        clean_text = response.text.strip() if response.text else "Gemini API returned no response."

        # Remove any remaining markdown-like symbols
        clean_text = re.sub(r"#\s*", "", clean_text)  # Remove '#' symbols
        clean_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean_text)  # Remove '**bold**'
        clean_text = re.sub(r"\*", "", clean_text)  # Remove '*' used for bullet points

        return clean_text # Return structured text
    except Exception as e:
        print(f"Gemini AI Formatting Error: {e}")
        return text  # If API fails, return raw text

def crawl_onion_site(url, keyword):
    """Crawl & Extract Cleaned Content from Onion Sites"""
    try:
        session = requests.Session()
        session.proxies = proxies
        response = session.get(url, timeout=20)

        if response.status_code != 200:
            return {"url": url, "error": "Failed to access the site"}

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract raw text
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
        raw_text = "\n\n".join(paragraphs)  # Separate paragraphs for readability

        # Use Gemini AI for formatting
        structured_text = format_text_with_gemini(raw_text)

        # Extract hyperlinks
        links = [a['href'] for a in soup.find_all('a', href=True) if ".onion" in a['href']]

        # Capture Screenshot
        screenshot_path = capture_screenshot(url)

        # Store in Database
        obj, created = OnionSite.objects.update_or_create(
            url=url,
            defaults={
                "extracted_text": structured_text[:10000],  # Store formatted text
                "hyperlinks": links,
                "keyword": keyword,
                "snapshot": screenshot_path,
                "crawl_date": datetime.datetime.now(),
            },
        )

        return {"url": url, "text": structured_text[:500], "links": links}  # Show preview text

    except requests.exceptions.RequestException as e:
        return {"url": url, "error": str(e)}
    
import requests
import concurrent.futures

# Define Tor proxy
TOR_PROXIES = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}
def check_onion_status(url):
    """
    Checks if the given Onion URL is reachable.
    Uses a timeout of 5 seconds per request.
    Returns (url, True) if live, (url, False) if dead.
    """
    try:
        response = requests.get(url, proxies=TOR_PROXIES, timeout=5)
        return (url, response.status_code == 200)  # ✅ Live if status code is 200
    except requests.exceptions.RequestException:
        return (url, False)  # ❌ Dead if request fails

def bulk_check_onion_status(urls, max_threads=20):
    """
    Checks the status of multiple Onion URLs in parallel.
    Uses a thread pool to speed up the checking process.
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_threads) as executor:
        # Submit all URLs for checking
        future_to_url = {executor.submit(check_onion_status, url): url for url in urls}

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_url):
            url, status = future.result()
            results.append({"url": url, "status": status})

    return results

def search_onion_links(request):
    """
    Fetches Onion links from search engines, removes unnecessary query params, and checks if they are live.
    """
    links = []
    if request.method == "POST":
        keyword = request.POST.get("keyword", "").strip()
        if not keyword:
            return render(request, "CrawlWeb.html", {"error": "Keyword is required", "search_results": links})

        headers = {"User-Agent": "Mozilla/5.0"}
        tor_proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }

        all_results = set()

        for engine in SEARCH_ENGINES:
            try:
                url = engine['html_url'].format(keyword)
                proxy = tor_proxies if engine.get('requires_tor', False) else None
                response = requests.get(url, headers=headers, proxies=proxy, timeout=30)

                if response.status_code != 200:
                    print(f"Skipping {engine['name']} (Status {response.status_code})")
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                for a in soup.find_all("a", href=True):
                    raw_link = a['href']

                    # Extract only the onion link from redirects
                    match = re.search(r'(https?://[a-zA-Z0-9.-]+\.onion)', raw_link)
                    clean_link = match.group(1) if match else raw_link

                    # Ensure it's a valid .onion URL without extra text
                    if ".onion" in clean_link and not re.search(r'\s', clean_link):
                        all_results.add(clean_link.strip())

            except requests.exceptions.RequestException as e:
                print(f"Error fetching from {engine['name']}: {e}")

        # ✅ Use multi-threading to check onion status
        search_results = bulk_check_onion_status(list(all_results), max_threads=20)

    return render(request, "CrawlWeb.html", {"search_results": search_results})

def clean_onion_links(onion_links):
    """
    Cleans and extracts valid Onion links from search results.
    """
    cleaned_links = []
    for title, link in onion_links:
        match = re.search(r"redirect_url=(http[s]?://[^\s]+)", link)
        if match:
            link = match.group(1)
        cleaned_links.append((title, link))

    unique_links = cleaned_links
    return unique_links

def get_onion_links(keyword):
    links = set()
    session = requests.Session()
    session.proxies = proxies

    for engine in SEARCH_ENGINES:
        try:
            response = session.get(engine + keyword, timeout=20)
            soup = BeautifulSoup(response.text, "html.parser")

            for a in soup.find_all('a', href=True):
                extracted_link = a['href']
                if ".onion" in extracted_link:
                    links.add(extracted_link)

        except Exception as e:
            print(f"❌ Error fetching from {engine}: {e}")

    return list(links)

import os
import subprocess

# Correct path to wkhtmltoimage
WKHTMLTOIMAGE_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe"

# Add wkhtmltoimage to the system PATH
os.environ["PATH"] += os.pathsep + os.path.dirname(WKHTMLTOIMAGE_PATH)

def capture_screenshot(url):
    """
    Captures a screenshot of a .onion site using wkhtmltoimage and Tor proxy.
    Saves the image in 'media/screenshots/'.
    """
    proxy = "socks5://127.0.0.1:9050"  # Tor Proxy
    output_dir = "media/screenshots/"
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

    # Generate filename from the URL
    filename = url.replace("http://", "").replace(".onion", "").replace("/", "_") + ".png"
    output_path = os.path.join(output_dir, filename)

    # Command formatted correctly for Windows
    command = [
        WKHTMLTOIMAGE_PATH, 
        "--proxy", proxy, 
        url, 
        output_path
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ Screenshot saved at: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Screenshot failed. Error: {e.stderr}")
        return None



def get_crawled_data(request):
    data = OnionSite.objects.all().values("url", "extracted_text", "hyperlinks", "crawl_date","snapshot")
    return JsonResponse(list(data), safe=False)

def CrawlWebAction(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')  # ✅ Get search keyword
        global crawl_links
        crawl_links = []

        web_url = request.POST.get('t1', False)
        web_url = web_url 
        crawl_links.append(web_url)

        print(f"🔍 Crawling: {web_url}")

        crawl_links = getLinks(crawl_links)  # ✅ Extract links

        print(f"🔗 Extracted {len(crawl_links)} onion links.")

        # ✅ Store results in database and display
        save = []
        extracted_links = []
        for i, link in enumerate(crawl_links):
            print(f"🚀 Processing {i+1}: {link}")

            # ✅ Call `crawl_onion_site` to fetch content & store in DB
            crawl_onion_site(link, keyword)

            extracted_links.append({"index": i+1, "url": link})
            save.append([link])

        # ✅ Save crawled links to CSV (Optional)
        save = pd.DataFrame(save, columns=['Crawled_Links'])
        save.to_csv("Crawled_Links.csv", index=False)

        print("✅ All links processed and stored in database!")

        context = {
        'current_view': 'CrawlWeb',
        'extracted_links': extracted_links,
        # other context variables
        }
        return render(request, "UserScreen.html", context)


# def CrawlWebAction(request):
#     if request.method == 'POST':
#         global crawl_links
#         crawl_links = []
#         web_url = request.POST.get('t1', False)
#         web_url = web_url+"/?product_tag=online+shopping"
#         crawl_links.append(web_url)
#         crawl_links = getLinks(crawl_links)
#         cols = ['Link No', 'Available Links in Darkweb URL']
#         output = '<table border="1" align="center" width="100%"><tr>'
#         font = '<font size="" color="black">'
#         for i in range(len(cols)):
#             output += "<td>"+font+cols[i]+"</font></td>"
#         output += "</tr>"
#         for i in range(len(crawl_links)):
#             output += "<tr><td>"+font+str(i+1)+"</font></td>"
#             output += "<td>"+font+crawl_links[i]+"</font></td></tr>"
#         output += "</table><br/><br/><br/><br/>"
#         save = []
#         for i in range(len(crawl_links)):
#             save.append([crawl_links[i]])
#         save = pd.DataFrame(save, columns = ['Crawled_Links'])
#         save.to_csv("Crawled_Links.csv", index=False)
#         context= {'data':output}
#         return render(request, "UserScreen.html", context)

def getText(links):
    output = ""
    try:
        for i in range(len(links)):
            data = requests.get(links[i],proxies=proxies).text
            soup = BeautifulSoup(data, "html.parser")
            text = soup.get_text()
            text = re.sub(r"\s+", " ", text)
            output += text.strip()
    except:
        print("Unreachable Url")
        pass        
    return output    

def TextExtraction(request):
    """Extract text from crawled Onion links and format it using Gemini AI."""
    global crawl_links, text_data

    if not crawl_links:  # ✅ Ensure it's not empty or undefined
        messages.error(request, "No crawled links available! Please crawl the dark web first.")
        return redirect("CrawlWeb")  # Redirect to the crawling page

    if request.method == 'GET':
        text_data = getText(crawl_links)  # Extract text from crawled links

        with open("Crawled_Text.txt", "wb") as file:
            file.write(text_data.encode())

        # Format extracted text using Gemini AI
        formatted_text = format_text_with_gemini(text_data)

        context = {
        'current_view': 'TextExtraction',
        'data': formatted_text,
        # other context variables
        }
        return render(request, "UserScreen.html", context)
    
from django.shortcuts import render
from .models import OnionSite

def ViewAllCrawled(request):
    all_data = OnionSite.objects.all().order_by('-crawl_date')  # Fetch all crawled .onion sites
    context = {'all_data': all_data}
    return render(request, "ViewAllCrawled.html", context)

def CrawledDetail(request, site_id):
    site = get_object_or_404(OnionSite, id=site_id)
    return render(request, "CrawledDetail.html", {'site': site})


def format_extracted_text(text):
    """
    Formats extracted text to improve readability:
    - Converts long paragraphs into bullet points or structured format.
    - Detects lists or product descriptions and converts them into a table.
    """
    # Split text into paragraphs
    paragraphs = text.split("\n\n")

    # Convert long paragraphs into a structured format
    formatted_paragraphs = []
    for para in paragraphs:
        if ":" in para or "GBP" in para:  # Likely a product list or structured data
            lines = para.split("\n")
            formatted_paragraphs.append("<ul class='list-disc pl-6 text-gray-300'>" + "".join(f"<li>{line}</li>" for line in lines) + "</ul>")
        else:
            formatted_paragraphs.append(f"<p class='mb-4 text-gray-300'>{para}</p>")

    return "".join(formatted_paragraphs)
def Category(request):
    if request.method == 'GET':
        global crawl_links, text_data, nlp
        ner_categories = ['PERSON', 'ORG', 'GPE', 'PRODUCT']
        category = {'PERSON':0, 'ORG':0, 'GPE':0, 'PRODUCT':0}
        doc = nlp(text_data)
        for ent in doc.ents:
            if ent.label_ in ner_categories:
                category[ent.label_] += 1
        cat = []
        count = []
        for key, value in category.items():
            cat.append(key.lower())
            count.append(value)
        plt.figure(figsize=(6,5))
        plt.pie(count, labels = cat, autopct='%.0f%%')
        plt.title("Darkweb Categorization Graph")
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()
        img_b64 = base64.b64encode(buf.getvalue()).decode()    
        context = {
        'current_view': 'Category',
        'img': img_b64,
        # other context variables
        }
        return render(request, 'UserScreen.html', context)
import json
import io
import base64
import matplotlib.pyplot as plt
import numpy as np
import spacy
from collections import Counter
from django.http import JsonResponse
from .models import OnionSite
from textblob import TextBlob

# Load Spacy model for Named Entity Recognition (NER)
nlp = spacy.load("en_core_web_sm")

def category_analysis(request):
    """
    Extracts data for visualization including:
    - Category Distribution (Pie Chart)
    - Sentiment Analysis (Gauge Chart)
    - Named Entity Recognition (Stacked Bar Chart)
    """

    # 1️⃣ **Category Distribution**
    categories = ["Marketplaces", "Hacking Forums", "Crypto Services", "Drugs", "Scams", "Others"]
    category_counts = {category: 0 for category in categories}
    
    # Define keyword categories
    category_keywords = {
        "Marketplaces": ["shop", "market", "vendor", "sell", "cart"],
        "Hacking Forums": ["exploit", "malware", "hacking", "ddos", "phishing"],
        "Crypto Services": ["bitcoin", "wallet", "crypto", "exchange"],
        "Drugs": ["cocaine", "meth", "drug", "weed", "pharma"],
        "Scams": ["fraud", "carding", "skimming", "fake", "stolen"]
    }

    extracted_texts = OnionSite.objects.values_list("extracted_text", flat=True)
    
    for text in extracted_texts:
        for category, keywords in category_keywords.items():
            if any(keyword in text.lower() for keyword in keywords):
                category_counts[category] += 1

    # Convert to list for JSON response
    category_data = [{"category": cat, "count": count} for cat, count in category_counts.items()]

    # 2️⃣ **Sentiment Analysis**
    sentiment_counts = {"Positive": 0, "Neutral": 0, "Negative": 0}

    for text in extracted_texts:
        analysis = TextBlob(text)
        if analysis.sentiment.polarity > 0.1:
            sentiment_counts["Positive"] += 1
        elif analysis.sentiment.polarity < -0.1:
            sentiment_counts["Negative"] += 1
        else:
            sentiment_counts["Neutral"] += 1

    sentiment_data = [{"sentiment": key, "count": value} for key, value in sentiment_counts.items()]

    # 3️⃣ **Named Entity Recognition (NER) Breakdown**
    ner_labels = ["PERSON", "ORG", "MONEY", "GPE", "PRODUCT"]
    ner_counts = {label: 0 for label in ner_labels}

    for text in extracted_texts:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ner_counts:
                ner_counts[ent.label_] += 1

    ner_data = [{"entity": label, "count": count} for label, count in ner_counts.items()]

    return JsonResponse({
        "category_distribution": category_data,
        "sentiment_analysis": sentiment_data,
        "ner_breakdown": ner_data
    })

from django.shortcuts import render
from .models import OnionSite
import datetime

from django.shortcuts import render
from .models import OnionSite
import datetime
from collections import Counter
import json

def dashboard(request):
    total_sites = OnionSite.objects.count()
    active_sites = OnionSite.objects.exclude(hyperlinks=[]).count()

    # Estimate Data Volume in MB
    total_text_size = sum(len(site.extracted_text) for site in OnionSite.objects.all())
    data_volume = round(total_text_size / (1024 * 1024), 2)

    # Recent Crawled Sites (Last 5)
    recent_sites = OnionSite.objects.order_by('-crawl_date')[:5]

    # Generate Data for Crawling Activity Chart (Last 7 Days)
    last_7_days = [datetime.date.today() - datetime.timedelta(days=i) for i in range(6, -1, -1)]
    crawling_labels = [date.strftime("%b %d") for date in last_7_days]
    crawling_data = [OnionSite.objects.filter(crawl_date__date=date).count() for date in last_7_days]

    # Extracted Text Analysis: Most Frequent Keywords
    all_text = " ".join(OnionSite.objects.values_list("extracted_text", flat=True)).lower()
    common_words = ["bitcoin", "market", "forum", "hacking", "service", "carding", "vpn", "crypto"]
    word_counts = Counter([word for word in all_text.split() if word in common_words])
    keyword_labels = list(word_counts.keys())
    keyword_data = list(word_counts.values())

    context = {
        "total_sites": total_sites,
        "active_sites": active_sites,
        "data_volume": data_volume,
        "recent_sites": recent_sites,
        "crawling_labels": json.dumps(crawling_labels),
        "crawling_data": json.dumps(crawling_data),
        "keyword_labels": json.dumps(keyword_labels),
        "keyword_data": json.dumps(keyword_data),
    }
    return render(request, "dashboard.html", context)



def user_logout(request):
    return render(request, "index.html")
from django.shortcuts import render
from collections import Counter
import re
from nltk.corpus import stopwords
from .models import OnionSite

stop_words = set(stopwords.words('english'))

def MostWords(request):
    """Analyzes the most frequently used words and sends them to the template for UI rendering."""
    
    # Fetch extracted text from database
    extracted_texts = OnionSite.objects.values_list("extracted_text", flat=True)

    if not extracted_texts:
        return render(request, "UserScreen.html", {"words": [], "counts": [], "current_view": "MostWords"})

    # Merge all extracted texts
    text_data = " ".join(extracted_texts)

    # Clean text (remove non-alphabetic characters)
    text_data_cleaned = re.sub(r'[^A-Za-z\s]', ' ', text_data.lower())  
    tokens = text_data_cleaned.split()

    # Remove stopwords and short words
    filtered_tokens = [w for w in tokens if w not in stop_words and len(w) > 2]

    # Count word occurrences
    word_counts = Counter(filtered_tokens)
    most_words = word_counts.most_common(15)  # Get top 15 words

    words_counts = [{"word": word, "count": count} for word, count in most_words]

    return render(request, "UserScreen.html", {
        "words_counts": words_counts,
        "current_view": "MostWords"
    })


def CrawlWeb(request):
    if request.method == 'GET':
       return render(request, 'CrawlWeb.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def UserLogin(request):
    if request.method == 'GET':
       return render(request, 'UserLogin.html', {}) 

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
@csrf_exempt  # ❌ Only use for debugging!
def UserLoginAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # Log the user in
            messages.success(request, f"Welcome, {username}!")
            return redirect('dashboard')  # ✅ Redirect to dashboard
        else:
            messages.error(request, "Invalid username or password")
            return render(request, "UserLogin.html", {})

    return render(request, "UserLogin.html", {})
