import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import pandas as pd
import webbrowser
from datetime import datetime


class AutocompleteEntry(tk.Entry):

    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)

    def autocomplete(self, delta=0):
        if delta:
            self.delete(self.position, tk.END)
        else:
            self.position = len(self.get())
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()):
                _hits.append(element)
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        if self._hits:
            self.delete(0, tk.END)
            self.insert(0, self._hits[self._hit_index])
            self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        """event handler for the keyrelease event on this widget"""
        if event.keysym == "BackSpace":
            self.delete(self.index(tk.INSERT), tk.END)
            self.position = self.index(tk.END)
        if event.keysym == "Left":
            if self.position < self.index(tk.END):
                self.delete(self.position, tk.END)
            else:
                self.position = self.position - 1
                self.delete(self.position, tk.END)
        if event.keysym == "Right":
            self.position = self.index(tk.END)
        if event.keysym == "Down":
            self.autocomplete(1)
        if event.keysym == "Up":
            self.autocomplete(-1)
        if len(event.keysym) == 1:
            self.autocomplete()


class AutocompleteCombobox(ttk.Combobox):

    def set_completion_list(self, completion_list):
        self._completion_list = sorted(completion_list, key=str.lower)
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = self._completion_list

    def autocomplete(self, delta=0):
        if delta:
            self.delete(self.position, tk.END)
        else:
            self.position = len(self.get())
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(self.get().lower()):
                _hits.append(element)
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        if self._hits:
            self.delete(0, tk.END)
            self.insert(0, self._hits[self._hit_index])
            self.select_range(self.position, tk.END)

    def handle_keyrelease(self, event):
        """event handler for the keyrelease event on this widget"""
        if event.keysym == "BackSpace":
            self.delete(self.index(tk.INSERT), tk.END)
            self.position = self.index(tk.END)
        if event.keysym == "Left":
            if self.position < self.index(tk.END):
                self.delete(self.position, tk.END)
            else:
                self.position = self.position - 1
                self.delete(self.position, tk.END)
        if event.keysym == "Right":
            self.position = self.index(tk.END)
        if len(event.keysym) == 1:
            self.autocomplete()


class GUI:
    def __init__(self, root, movies):
        self.root = root
        self.root.title("Movie Recommender")
        self.names = movies["movie_title"].astype("string").dropna().to_list()
        self.names.sort()
        self.movieRatings = {}
        self.initialize_ui()
        self.movies = movies

    def initialize_ui(self):
        self.root.geometry("600x400")
        self.root.resizable(True, True)

        ttk.Label(self.root, text="Enter Movie Reviews").pack()

        self.combobox = AutocompleteCombobox(self.root)
        self.combobox.set_completion_list(self.names)
        self.combobox.pack(fill=tk.X, pady=5)

        ttk.Label(self.root, text="Rating:").pack()
        self.rating_entry = ttk.Entry(self.root)
        self.rating_entry.pack(pady=5)

        ttk.Button(self.root, text="Add Review", command=self.add_review).pack(pady=5)

        self.reviewed_movies_list = tk.Listbox(self.root, selectmode=tk.SINGLE)
        self.reviewed_movies_list.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Button(self.root, text="Remove from List", command=self.remove_review).pack(pady=5)

        ttk.Button(self.root, text="Recommend", command=self.recommend_movies).pack(pady=5)

    def add_review(self):
            movie = self.combobox.get()
            rating = self.rating_entry.get()

            if not movie or not rating:
                messagebox.showerror("Error", "Please enter both movie and rating.")
                return

            if movie not in self.names:
                messagebox.showerror("Error", "Please enter a valid movie.")
                return

            movie_id = self.movies.loc[self.movies['movie_title'] == movie]['movieID'].iloc[0]

            if movie_id in self.movieRatings:
                messagebox.showerror("Error", "Movie already selected.")
            else:
                try:
                    rating = int(rating)
                    if rating < 0 or rating > 10:
                        messagebox.showerror("Error", "Rating must be between 0 and 10.")
                    else:
                        self.movieRatings[movie_id] = rating
                        self.reviewed_movies_list.insert(tk.END, f"{movie} (Rating: {rating})")
                except ValueError:
                    messagebox.showerror("Error", "Rating must be an integer.")

    def remove_review(self):
        selected_index = self.reviewed_movies_list.curselection()
        if selected_index:
            selected_movie = self.reviewed_movies_list.get(selected_index)
            movie = selected_movie.split(" (Rating:")[0]
            movie_id = self.movies.loc[self.movies['movie_title'] == movie]['movieID'].iloc[0]
            del self.movieRatings[movie_id]
            self.reviewed_movies_list.delete(selected_index)

    def recommend_movies(self):
        if len(self.movieRatings) < 3:
            messagebox.showerror("Error", "Please select at least 3 movies!")
        else:
            recommended_movies = self.get_recommendations()
            popup = tk.Toplevel(self.root)
            popup.geometry("300x200")
            popup.resizable(True, True)
            popup.title("Recommended Movies")

            for movieID in recommended_movies:
                movie_title = self.movies.loc[self.movies['movieID'] == movieID]['movie_title'].iloc[0]
                imdb_link = self.movies.loc[self.movies['movieID'] == movieID]['imdb_link'].iloc[0]
                link_label = tk.Label(popup, text=movie_title, cursor="hand2", fg="blue")
                link_label.pack(fill=tk.BOTH, expand=True, pady=5)
                link_label.bind("<Button-1>", lambda event, url=imdb_link: self.open_link(url))

            popup.update_idletasks()
            width = popup.winfo_width()
            height = popup.winfo_height()
            x = self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2
            popup.geometry(f"{width}x{height}+{x}+{y}")

    def open_link(self, url):
        webbrowser.open_new(url)

    def get_recommendations(self):
        reviewDB = pd.read_csv("movie_ratings.csv")
        reviewDB = reviewDB.pivot_table(index='movieID', columns='userID', values='rating')
        print(self.movieRatings)
        userRatings = pd.DataFrame.from_dict(self.movieRatings, orient='index', columns=['rating'])
        userRatings.reset_index(inplace=True, names='movieID')
        userID = reviewDB.columns.max()+1
        userRatings['userID'] = userID
        userRatings = userRatings.pivot_table(index='movieID', columns='userID', values='rating')
        reviewDB[userID] = userRatings[userID]
        reviewDB.fillna(5, inplace=True)
        print(reviewDB)
        userRatings = reviewDB[userID]
        corr = reviewDB.corrwith(userRatings, numeric_only=True)
        corr = pd.DataFrame(corr, columns=["Correlation"])
        corr.sort_values('Correlation', ascending=False, inplace=True)
        corr.drop(userID, inplace=True)
        print(corr)
        movieRecommendations = reviewDB[corr.index[0]]
        movieRecommendations = movieRecommendations[[movieID not in self.movieRatings for movieID in movieRecommendations.index]]
        movieRecommendations = movieRecommendations.nlargest(5).index.to_list()
        print(movieRecommendations)
        return movieRecommendations

def main():
    movies = pd.read_csv("movie_database.csv")
    root = tk.Tk()
    app = GUI(root, movies)
    root.mainloop()

if __name__ == "__main__":
    main()