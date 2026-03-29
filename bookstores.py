import geocoder
import webbrowser


def find_nearby_bookstores():
    print("Detecting your location...")

    # Auto-detect location via IP
    g = geocoder.ip('me')

    if g.ok:
        lat, lng = g.latlng
        print(f"Location found: {g.city}, {g.country}")

        # Build Google Maps URL for nearby bookstores
        query = "bookstores+near+me"
        url = f"https://www.google.com/maps/search/{query}/@{lat},{lng},14z"

        print("Opening Google Maps in your browser...")
        webbrowser.open(url)
    else:
        print("Could not detect location. Opening general search instead...")
        webbrowser.open("https://www.google.com/maps/search/bookstores+near+me")


if __name__ == "__main__":
    find_nearby_bookstores()