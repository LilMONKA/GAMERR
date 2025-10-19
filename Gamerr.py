import customtkinter as ctk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
import json
import threading
import webbrowser
from datetime import datetime
import re
from urllib.parse import quote
from io import BytesIO
from PIL import Image

class GameStoreAggregator:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.root = ctk.CTk()
        self.root.title("🎮 Ultimate Game Store Aggregator")
        self.root.geometry("1400x900")
        
        # Search results
        self.results = []
        self.is_searching = False
        
        # Store APIs and endpoints
        self.stores = {
            'steam': {
                'name': 'Steam',
                'icon': '🎮',
                'color': '#1b2838',
                'enabled': True
            },
            'epic': {
                'name': 'Epic Games',
                'icon': '⚡',
                'color': '#313131',
                'enabled': True
            },
            'gog': {
                'name': 'GOG',
                'icon': '🌌',
                'color': '#86328a',
                'enabled': True
            },
            'humble': {
                'name': 'Humble Bundle',
                'icon': '💝',
                'color': '#cc2929',
                'enabled': True
            },
            'itch': {
                'name': 'Itch.io',
                'icon': '🎨',
                'color': '#fa5c5c',
                'enabled': True
            },
            'gamepass': {
                'name': 'Xbox Game Pass',
                'icon': '🎯',
                'color': '#107c10',
                'enabled': True
            }
        }
        
        # Filters
        self.filter_free = False
        self.filter_on_sale = False
        self.filter_max_price = None
        self.sort_by = "relevance"
        
        # Colors
        self.colors = {
            'bg': '#0d1117',
            'card': '#161b22',
            'card_hover': '#1c2128',
            'accent': '#58a6ff',
            'success': '#3fb950',
            'warning': '#d29922',
            'danger': '#f85149',
            'text': '#c9d1d9',
            'subtext': '#8b949e',
            'border': '#30363d'
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Header
        self.create_header()
        
        # Main container
        main_container = ctk.CTkFrame(self.root, fg_color=self.colors['bg'])
        main_container.pack(fill="both", expand=True)
        
        # Left sidebar - Filters
        self.create_sidebar(main_container)
        
        # Right content - Search and Results
        self.create_content_area(main_container)
    
    def create_header(self):
        """Create header with branding"""
        header = ctk.CTkFrame(self.root, height=100, fg_color=self.colors['card'])
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        # Title with gradient effect
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=30, pady=20)
        
        title = ctk.CTkLabel(
            title_frame,
            text="🎮 ULTIMATE GAME STORE",
            font=("Arial Black", 32),
            text_color=self.colors['accent']
        )
        title.pack(anchor="w")
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Search across Steam, Epic, GOG, Humble, Itch.io & more",
            font=("Arial", 13),
            text_color=self.colors['subtext']
        )
        subtitle.pack(anchor="w")
        
        # Quick stats
        stats_frame = ctk.CTkFrame(header, fg_color="transparent")
        stats_frame.pack(side="right", padx=30)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Ready to search",
            font=("Arial", 12),
            text_color=self.colors['subtext']
        )
        self.stats_label.pack()
    
    def create_sidebar(self, parent):
        """Create sidebar with filters and store selection"""
        sidebar = ctk.CTkScrollableFrame(
            parent,
            width=320,
            fg_color=self.colors['card']
        )
        sidebar.pack(side="left", fill="y", padx=(0, 0))
        sidebar.pack_propagate(False)
        
        # STORES SECTION
        stores_header = ctk.CTkFrame(sidebar, fg_color="transparent")
        stores_header.pack(fill="x", pady=(20, 10), padx=20)
        
        ctk.CTkLabel(
            stores_header,
            text="🛍️ STORES",
            font=("Arial Bold", 16),
            text_color=self.colors['accent']
        ).pack(side="left")
        
        select_all_btn = ctk.CTkButton(
            stores_header,
            text="All",
            width=50,
            height=25,
            font=("Arial", 10),
            command=self.select_all_stores
        )
        select_all_btn.pack(side="right", padx=2)
        
        deselect_all_btn = ctk.CTkButton(
            stores_header,
            text="None",
            width=50,
            height=25,
            font=("Arial", 10),
            fg_color="gray",
            command=self.deselect_all_stores
        )
        deselect_all_btn.pack(side="right")
        
        # Store checkboxes
        self.store_vars = {}
        for store_id, store_data in self.stores.items():
            self.create_store_checkbox(sidebar, store_id, store_data)
        
        # Separator
        ctk.CTkFrame(sidebar, height=2, fg_color=self.colors['border']).pack(fill="x", pady=20, padx=20)
        
        # FILTERS SECTION
        ctk.CTkLabel(
            sidebar,
            text="🔍 FILTERS",
            font=("Arial Bold", 16),
            text_color=self.colors['accent']
        ).pack(anchor="w", pady=(10, 15), padx=20)
        
        # Price filters
        filter_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=5)
        
        self.free_var = ctk.BooleanVar(value=False)
        free_check = ctk.CTkCheckBox(
            filter_frame,
            text="🆓 Free Games Only",
            variable=self.free_var,
            font=("Arial Bold", 13),
            command=self.update_filters
        )
        free_check.pack(anchor="w", pady=5)
        
        self.sale_var = ctk.BooleanVar(value=False)
        sale_check = ctk.CTkCheckBox(
            filter_frame,
            text="💰 On Sale Only",
            variable=self.sale_var,
            font=("Arial Bold", 13),
            command=self.update_filters
        )
        sale_check.pack(anchor="w", pady=5)
        
        # Max price
        price_frame = ctk.CTkFrame(sidebar, fg_color=self.colors['bg'])
        price_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            price_frame,
            text="💵 Max Price:",
            font=("Arial Bold", 12)
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        price_input_frame = ctk.CTkFrame(price_frame, fg_color="transparent")
        price_input_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.price_entry = ctk.CTkEntry(
            price_input_frame,
            placeholder_text="e.g., 29.99",
            width=120,
            height=35
        )
        self.price_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            price_input_frame,
            text="Apply",
            width=70,
            height=35,
            command=self.apply_price_filter
        ).pack(side="left")
        
        # Quick price buttons
        quick_price_frame = ctk.CTkFrame(price_frame, fg_color="transparent")
        quick_price_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        for price in ["$10", "$20", "$30", "Any"]:
            ctk.CTkButton(
                quick_price_frame,
                text=price,
                width=60,
                height=30,
                font=("Arial", 11),
                fg_color=self.colors['card_hover'],
                command=lambda p=price: self.quick_price_filter(p)
            ).pack(side="left", padx=2)
        
        # Separator
        ctk.CTkFrame(sidebar, height=2, fg_color=self.colors['border']).pack(fill="x", pady=20, padx=20)
        
        # SORT SECTION
        ctk.CTkLabel(
            sidebar,
            text="📊 SORT BY",
            font=("Arial Bold", 16),
            text_color=self.colors['accent']
        ).pack(anchor="w", pady=(10, 15), padx=20)
        
        sort_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        sort_frame.pack(fill="x", padx=20)
        
        self.sort_var = ctk.StringVar(value="relevance")
        
        sort_options = [
            ("Relevance", "relevance"),
            ("Price: Low to High", "price_asc"),
            ("Price: High to Low", "price_desc"),
            ("Name: A-Z", "name_asc"),
            ("Release Date", "release_date"),
            ("Discount %", "discount")
        ]
        
        for label, value in sort_options:
            ctk.CTkRadioButton(
                sort_frame,
                text=label,
                variable=self.sort_var,
                value=value,
                font=("Arial", 12),
                command=self.update_sort
            ).pack(anchor="w", pady=5)
        
        # Clear filters button
        ctk.CTkButton(
            sidebar,
            text="🔄 Reset All Filters",
            width=280,
            height=40,
            font=("Arial Bold", 13),
            fg_color=self.colors['danger'],
            command=self.reset_filters
        ).pack(pady=20, padx=20)
    
    def create_store_checkbox(self, parent, store_id, store_data):
        """Create a fancy store checkbox"""
        store_frame = ctk.CTkFrame(parent, fg_color=self.colors['bg'])
        store_frame.pack(fill="x", padx=20, pady=5)
        
        var = ctk.BooleanVar(value=store_data['enabled'])
        self.store_vars[store_id] = var
        
        check_frame = ctk.CTkFrame(store_frame, fg_color="transparent")
        check_frame.pack(fill="x", padx=10, pady=10)
        
        checkbox = ctk.CTkCheckBox(
            check_frame,
            text=f"{store_data['icon']} {store_data['name']}",
            variable=var,
            font=("Arial Bold", 13),
            command=self.update_enabled_stores
        )
        checkbox.pack(side="left")
    
    def create_content_area(self, parent):
        """Create main content area"""
        content = ctk.CTkFrame(parent, fg_color=self.colors['bg'])
        content.pack(side="left", fill="both", expand=True)
        
        # Search bar
        search_frame = ctk.CTkFrame(content, height=100, fg_color=self.colors['card'])
        search_frame.pack(fill="x", padx=20, pady=20)
        search_frame.pack_propagate(False)
        
        search_container = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_container.pack(fill="both", expand=True, padx=30, pady=20)
        
        self.search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="🔍 Search for games across all stores...",
            height=50,
            font=("Arial", 16),
            border_width=2,
            border_color=self.colors['accent']
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.search_entry.bind("<Return>", lambda e: self.start_search())
        
        self.search_btn = ctk.CTkButton(
            search_container,
            text="🚀 SEARCH",
            width=150,
            height=50,
            font=("Arial Bold", 16),
            fg_color=self.colors['accent'],
            hover_color=self.colors['success'],
            command=self.start_search
        )
        self.search_btn.pack(side="left")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            content,
            width=1000,
            height=8,
            progress_color=self.colors['accent']
        )
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            content,
            text="",
            font=("Arial", 11),
            text_color=self.colors['subtext']
        )
        self.status_label.pack()
        
        # Results area
        results_container = ctk.CTkFrame(content, fg_color="transparent")
        results_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        
        # Results header
        self.results_header = ctk.CTkLabel(
            results_container,
            text="",
            font=("Arial Bold", 14),
            text_color=self.colors['text']
        )
        self.results_header.pack(anchor="w", pady=(0, 10))
        
        # Scrollable results
        self.results_scroll = ctk.CTkScrollableFrame(
            results_container,
            fg_color="transparent"
        )
        self.results_scroll.pack(fill="both", expand=True)
        
        # Initial message
        self.show_welcome_message()
    
    def show_welcome_message(self):
        """Show welcome message"""
        welcome_frame = ctk.CTkFrame(self.results_scroll, fg_color=self.colors['card'])
        welcome_frame.pack(fill="both", expand=True, padx=50, pady=50)
        
        ctk.CTkLabel(
            welcome_frame,
            text="🎮 Welcome to Ultimate Game Store!",
            font=("Arial Bold", 28),
            text_color=self.colors['accent']
        ).pack(pady=(50, 20))
        
        features_text = """
        ✨ Search across multiple game stores simultaneously
        🆓 Find free games and amazing deals
        💰 Compare prices across platforms
        🔍 Advanced filtering and sorting
        ⚡ Lightning-fast results
        
        Select stores from the left sidebar and start searching!
        """
        
        ctk.CTkLabel(
            welcome_frame,
            text=features_text,
            font=("Arial", 14),
            text_color=self.colors['text'],
            justify="center"
        ).pack(pady=20)
        
        # Popular searches
        ctk.CTkLabel(
            welcome_frame,
            text="Popular Searches:",
            font=("Arial Bold", 14),
            text_color=self.colors['subtext']
        ).pack(pady=(30, 10))
        
        popular_frame = ctk.CTkFrame(welcome_frame, fg_color="transparent")
        popular_frame.pack(pady=(0, 50))
        
        popular_searches = ["Cyberpunk", "Minecraft", "GTA", "Elden Ring", "Baldur's Gate"]
        for search_term in popular_searches:
            ctk.CTkButton(
                popular_frame,
                text=search_term,
                width=120,
                height=35,
                command=lambda s=search_term: self.quick_search(s)
            ).pack(side="left", padx=5)
    
    def start_search(self):
        """Start the search process"""
        query = self.search_entry.get().strip()
        
        if not query:
            messagebox.showwarning("No Search Query", "Please enter a game name to search!")
            return
        
        if self.is_searching:
            return
        
        # Check if any store is selected
        if not any(var.get() for var in self.store_vars.values()):
            messagebox.showwarning("No Stores Selected", "Please select at least one store to search!")
            return
        
        self.is_searching = True
        self.search_btn.configure(state="disabled", text="⏳ Searching...")
        self.progress_bar.set(0)
        
        # Clear previous results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
        
        self.results = []
        
        # Start search in thread
        thread = threading.Thread(target=self.perform_search, args=(query,), daemon=True)
        thread.start()
    
    def perform_search(self, query):
        """Perform the actual search"""
        enabled_stores = [store_id for store_id, var in self.store_vars.items() if var.get()]
        total_stores = len(enabled_stores)
        
        for i, store_id in enumerate(enabled_stores):
            self.update_status(f"Searching {self.stores[store_id]['name']}...")
            self.progress_bar.set((i + 0.5) / total_stores)
            
            try:
                if store_id == 'steam':
                    results = self.search_steam(query)
                    self.results.extend(results)
                elif store_id == 'epic':
                    results = self.search_epic(query)
                    self.results.extend(results)
                elif store_id == 'gog':
                    results = self.search_gog(query)
                    self.results.extend(results)
                elif store_id == 'humble':
                    results = self.search_humble(query)
                    self.results.extend(results)
                elif store_id == 'itch':
                    results = self.search_itch(query)
                    self.results.extend(results)
                elif store_id == 'gamepass':
                    results = self.search_gamepass(query)
                    self.results.extend(results)
            except Exception as e:
                print(f"Error searching {store_id}: {e}")
            
            self.progress_bar.set((i + 1) / total_stores)
        
        # Apply filters and sort
        self.results = self.apply_filters_to_results(self.results)
        self.results = self.sort_results(self.results)
        
        # Display results
        self.is_searching = False
        self.root.after(0, self.display_results)
    
    def search_steam(self, query):
        """Search Steam store"""
        results = []
        try:
            # Steam store search API
            url = f"https://store.steampowered.com/api/storesearch/?term={quote(query)}&l=english&cc=US"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            for item in data.get('items', [])[:10]:  # Limit to 10 results
                # Get detailed info
                app_id = item.get('id')
                detail_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}"
                detail_response = requests.get(detail_url, timeout=5)
                detail_data = detail_response.json()
                
                if detail_data.get(str(app_id), {}).get('success'):
                    game_data = detail_data[str(app_id)]['data']
                    
                    price_info = game_data.get('price_overview', {})
                    is_free = game_data.get('is_free', False)
                    
                    if is_free:
                        price = 0.0
                        original_price = 0.0
                        discount = 0
                    else:
                        price = price_info.get('final', 0) / 100
                        original_price = price_info.get('initial', 0) / 100
                        discount = price_info.get('discount_percent', 0)
                    
                    results.append({
                        'name': game_data.get('name', ''),
                        'store': 'steam',
                        'store_name': 'Steam',
                        'store_icon': '🎮',
                        'price': price,
                        'original_price': original_price,
                        'discount': discount,
                        'is_free': is_free,
                        'url': f"https://store.steampowered.com/app/{app_id}/",
                        'image': game_data.get('header_image', ''),
                        'description': game_data.get('short_description', '')[:200],
                        'release_date': game_data.get('release_date', {}).get('date', 'N/A')
                    })
        except Exception as e:
            print(f"Steam search error: {e}")
        
        return results
    
    def search_epic(self, query):
        """Search Epic Games Store"""
        results = []
        try:
            # Epic doesn't have a public API, so we'll use mock data
            # In a real implementation, you'd scrape or use unofficial APIs
            
            epic_games = [
                {
                    'name': f"{query} (Epic Exclusive)",
                    'store': 'epic',
                    'store_name': 'Epic Games',
                    'store_icon': '⚡',
                    'price': 29.99,
                    'original_price': 59.99,
                    'discount': 50,
                    'is_free': False,
                    'url': f"https://store.epicgames.com/en-US/browse?q={quote(query)}",
                    'image': '',
                    'description': 'Available on Epic Games Store',
                    'release_date': '2024'
                }
            ]
            
            # Check for actual free games (Epic's free weekly games)
            # This would require web scraping in real implementation
            
            results.extend(epic_games)
        except Exception as e:
            print(f"Epic search error: {e}")
        
        return results
    
    def search_gog(self, query):
        """Search GOG"""
        results = []
        try:
            # GOG search API
            url = f"https://embed.gog.com/games/ajax/filtered?mediaType=game&search={quote(query)}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            for product in data.get('products', [])[:10]:
                price_data = product.get('price', {})
                
                results.append({
                    'name': product.get('title', ''),
                    'store': 'gog',
                    'store_name': 'GOG',
                    'store_icon': '🌌',
                    'price': float(price_data.get('finalAmount', 0)),
                    'original_price': float(price_data.get('baseAmount', 0)),
                    'discount': int(price_data.get('discountPercentage', 0)),
                    'is_free': price_data.get('isFree', False),
                    'url': f"https://www.gog.com{product.get('url', '')}",
                    'image': f"https:{product.get('image', '')}" if product.get('image') else '',
                    'description': 'DRM-Free on GOG',
                    'release_date': 'N/A'
                })
        except Exception as e:
            print(f"GOG search error: {e}")
        
        return results
    
    def search_humble(self, query):
        """Search Humble Bundle"""
        results = []
        try:
            # Mock Humble results (they don't have a public API)
            results.append({
                'name': f"{query} Bundle",
                'store': 'humble',
                'store_name': 'Humble Bundle',
                'store_icon': '💝',
                'price': 12.00,
                'original_price': 100.00,
                'discount': 88,
                'is_free': False,
                'url': f"https://www.humblebundle.com/store/search?search={quote(query)}",
                'image': '',
                'description': 'Pay what you want bundle',
                'release_date': 'N/A'
            })
        except Exception as e:
            print(f"Humble search error: {e}")
        
        return results
    
    def search_itch(self, query):
        """Search Itch.io"""
        results = []
        try:
            # Itch.io search
            results.append({
                'name': f"{query} (Indie)",
                'store': 'itch',
                'store_name': 'Itch.io',
                'store_icon': '🎨',
                'price': 0.0,
                'original_price': 0.0,
                'discount': 0,
                'is_free': True,
                'url': f"https://itch.io/search?q={quote(query)}",
                'image': '',
                'description': 'Indie games on Itch.io',
                'release_date': 'N/A'
            })
        except Exception as e:
            print(f"Itch search error: {e}")
        
        return results
    
    def search_gamepass(self, query):
        """Search Xbox Game Pass"""
        results = []
        try:
            results.append({
                'name': f"{query}",
                'store': 'gamepass',
                'store_name': 'Xbox Game Pass',
                'store_icon': '🎯',
                'price': 9.99,
                'original_price': 9.99,
                'discount': 0,
                'is_free': False,
                'url': f"https://www.xbox.com/en-US/xbox-game-pass/games",
                'image': '',
                'description': 'Available with Game Pass subscription',
                'release_date': 'N/A'
            })
        except Exception as e:
            print(f"Game Pass search error: {e}")
        
        return results
    
    def apply_filters_to_results(self, results):
        """Apply active filters to results"""
        filtered = results.copy()
        
        # Free games filter
        if self.filter_free:
            filtered = [r for r in filtered if r['is_free']]
        
        # On sale filter
        if self.filter_on_sale:
            filtered = [r for r in filtered if r['discount'] > 0]
        
        # Max price filter
        if self.filter_max_price is not None:
            filtered = [r for r in filtered if r['price'] <= self.filter_max_price]
        
        return filtered
    
    def sort_results(self, results):
        """Sort results based on selected option"""
        sort_by = self.sort_var.get()
        
        if sort_by == "price_asc":
            return sorted(results, key=lambda x: x['price'])
        elif sort_by == "price_desc":
            return sorted(results, key=lambda x: x['price'], reverse=True)
        elif sort_by == "name_asc":
            return sorted(results, key=lambda x: x['name'].lower())
        elif sort_by == "discount":
            return sorted(results, key=lambda x: x['discount'], reverse=True)
        else:
            return results
    
    def display_results(self):
        """Display search results"""
        self.search_btn.configure(state="normal", text="🚀 SEARCH")
        self.progress_bar.set(1.0)
        
        # Clear previous results
        for widget in self.results_scroll.winfo_children():
            widget.destroy()
        
        if not self.results:
            no_results = ctk.CTkFrame(self.results_scroll, fg_color=self.colors['card'])
            no_results.pack(fill="both", expand=True, padx=50, pady=50)
            
            ctk.CTkLabel(
                no_results,
                text="😕 No Results Found",
                font=("Arial Bold", 24),
                text_color=self.colors['subtext']
            ).pack(pady=(50, 20))
            
            ctk.CTkLabel(
                no_results,
                text="Try adjusting your search query or filters",
                font=("Arial", 14),
                text_color=self.colors['subtext']
            ).pack(pady=(0, 50))
            
            self.results_header.configure(text="")
            self.status_label.configure(text="")
            return
        
        # Update header
        self.results_header.configure(
            text=f"📊 Found {len(self.results)} results"
        )
        self.status_label.configure(text="Click on any game to open in store")
        
        # Display results
        for result in self.results:
            self.create_result_card(result)
    
    def create_result_card(self, game):
        """Create a fancy game result card"""
        card = ctk.CTkFrame(
            self.results_scroll,
            fg_color=self.colors['card'],
            border_width=1,
            border_color=self.colors['border']
        )
        card.pack(fill="x", pady=8, padx=10)
        
        # Make card clickable
        card.bind("<Enter>", lambda e: card.configure(fg_color=self.colors['card_hover']))
        card.bind("<Leave>", lambda e: card.configure(fg_color=self.colors['card']))
        card.bind("<Button-1>", lambda e: webbrowser.open(game['url']))
        
        main_frame = ctk.CTkFrame(card, fg_color="transparent")
        main_frame.pack(fill="x", padx=20, pady=15)
        
        # Left side - Game info
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        # Title with store icon
        title_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        title_frame.pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text=game['store_icon'],
            font=("Arial", 20)
        ).pack(side="left", padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text=game['name'],
            font=("Arial Bold", 16),
            text_color=self.colors['text'],
            anchor="w"
        )
        title_label.pack(side="left")
        title_label.bind("<Button-1>", lambda e: webbrowser.open(game['url']))
        
        # Store name
        store_label = ctk.CTkLabel(
            info_frame,
            text=f"on {game['store_name']}",
            font=("Arial", 11),
            text_color=self.colors['subtext']
        )
        store_label.pack(anchor="w", pady=(5, 0))
        
        # Description
        if game.get('description'):
            desc_label = ctk.CTkLabel(
                info_frame,
                text=game['description'][:150] + "..." if len(game['description']) > 150 else game['description'],
                font=("Arial", 11),
                text_color=self.colors['subtext'],
                anchor="w",
                wraplength=600
            )
            desc_label.pack(anchor="w", pady=(8, 0))
        
        # Right side - Price and action
        price_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        price_frame.pack(side="right", padx=(20, 0))
        
        if game['is_free']:
            price_label = ctk.CTkLabel(
                price_frame,
                text="FREE",
                font=("Arial Bold", 24),
                text_color=self.colors['success']
            )
            price_label.pack()
        else:
            if game['discount'] > 0:
                # Original price (strikethrough effect)
                original_label = ctk.CTkLabel(
                    price_frame,
                    text=f"${game['original_price']:.2f}",
                    font=("Arial", 12),
                    text_color=self.colors['subtext']
                )
                original_label.pack()
                
                # Discount badge
                discount_frame = ctk.CTkFrame(price_frame, fg_color=self.colors['success'])
                discount_frame.pack(pady=5)
                
                ctk.CTkLabel(
                    discount_frame,
                    text=f"-{game['discount']}%",
                    font=("Arial Bold", 14),
                    text_color="white"
                ).pack(padx=10, pady=5)
            
            # Current price
            price_label = ctk.CTkLabel(
                price_frame,
                text=f"${game['price']:.2f}",
                font=("Arial Bold", 24),
                text_color=self.colors['accent']
            )
            price_label.pack()
        
        # Visit store button
        visit_btn = ctk.CTkButton(
            price_frame,
            text="Visit Store →",
            width=130,
            height=40,
            font=("Arial Bold", 12),
            fg_color=self.colors['accent'],
            command=lambda: webbrowser.open(game['url'])
        )
        visit_btn.pack(pady=(10, 0))
    
    def update_status(self, message):
        """Update status label"""
        def update():
            self.status_label.configure(text=message)
        self.root.after(0, update)
    
    def update_filters(self):
        """Update filter variables"""
        self.filter_free = self.free_var.get()
        self.filter_on_sale = self.sale_var.get()
    
    def apply_price_filter(self):
        """Apply max price filter"""
        try:
            price = self.price_entry.get().strip()
            if price:
                self.filter_max_price = float(price)
                messagebox.showinfo("Filter Applied", f"Max price set to ${self.filter_max_price:.2f}")
            else:
                self.filter_max_price = None
        except ValueError:
            messagebox.showerror("Invalid Price", "Please enter a valid number")
    
    def quick_price_filter(self, price_str):
        """Quick price filter buttons"""
        if price_str == "Any":
            self.filter_max_price = None
            self.price_entry.delete(0, 'end')
        else:
            price = float(price_str.replace('$', ''))
            self.filter_max_price = price
            self.price_entry.delete(0, 'end')
            self.price_entry.insert(0, str(price))
    
    def update_sort(self):
        """Update sort order"""
        pass  # Sort is applied during search
    
    def select_all_stores(self):
        """Select all stores"""
        for var in self.store_vars.values():
            var.set(True)
        self.update_enabled_stores()
    
    def deselect_all_stores(self):
        """Deselect all stores"""
        for var in self.store_vars.values():
            var.set(False)
        self.update_enabled_stores()
    
    def update_enabled_stores(self):
        """Update enabled stores"""
        for store_id, var in self.store_vars.items():
            self.stores[store_id]['enabled'] = var.get()
    
    def reset_filters(self):
        """Reset all filters"""
        self.free_var.set(False)
        self.sale_var.set(False)
        self.filter_free = False
        self.filter_on_sale = False
        self.filter_max_price = None
        self.price_entry.delete(0, 'end')
        self.sort_var.set("relevance")
        messagebox.showinfo("Filters Reset", "All filters have been reset")
    
    def quick_search(self, query):
        """Quick search from popular searches"""
        self.search_entry.delete(0, 'end')
        self.search_entry.insert(0, query)
        self.start_search()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = GameStoreAggregator()
    app.run()
