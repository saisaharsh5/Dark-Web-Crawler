import requests
from bs4 import BeautifulSoup
import stem.connection
from stem import Signal
import time

def crawl_onion_site(onion_url, output_file="onion_data.txt"):
    """Crawls data from an onion link and saves it to a text file.

    Args:
        onion_url: The onion URL to crawl (e.g., "http://xxxxxxxx.onion").
        output_file: The name of the text file to save the data to.
    """

    try:
        # 1. Start Tor service (if not already running) - Simplified for demonstration
        # In a real application, you'd likely use a more robust Tor control setup
        # using the stem library.
        # This example assumes Tor is running.
        # For more details on Tor integration, see the advanced section below.

        # 2. Set up a Tor proxy
        socks_port = 9050 # Default Tor SOCKS port
        control_port = 9051 # Default Tor Control Port

        proxies = {
            'http': f'socks5://127.0.0.1:9050',
            'https': f'socks5://127.0.0.1:9050'
        }

        # 3. Make the request through the Tor proxy
        print(f"Crawling: {onion_url}")
        response = requests.get(onion_url, proxies=proxies, timeout=10) # Timeout is important!
        response.raise_for_status()  # Check for HTTP errors (4xx or 5xx)

        # 4. Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # 5. Extract the data you want (example: all text from the page)
        extracted_text = soup.get_text(strip=True) # strip=True removes extra whitespace


        # 6. Save the extracted data to the text file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        print(f"Data saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error crawling {onion_url}: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example usage:
onion_link = "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion"  # Replace with a real onion link!
crawl_onion_site(onion_link)



# --- Advanced (Tor Control with Stem - Recommended for Real Applications) ---
# The simplified Tor start above is just for demonstration.  For production, use
# the stem library to control Tor more directly.

# Example (you'll need to install stem: pip install stem):

# from stem import Controller
# from stem import Signal

# def start_tor():
#     # ... (Code to start Tor using stem, handle data directory, etc.) ...
#     pass

# def renew_tor_circuit():
#     with Controller.from_port(port=9051) as controller:  # Your control port
#         controller.authenticate("your_control_password")  # If you've set one
#         controller.signal(Signal.NEWNYM)  # Renew circuit (get new IP)
#         print("Tor circuit renewed.")

# # ... (In your crawl_onion_site function) ...
# # start_tor()  # If Tor isn't already running
# # renew_tor_circuit() # Before each request, or periodically