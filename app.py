import streamlit as st
import pickle
import pandas as pd  # You forgot to import pandas as pd
import requests
import regex as re
import base64

# Load the similarity matrix and movies list
similarity = pickle.load(open('similarity.pkl', 'rb'))
movies_list = pickle.load(open('movies.pkl', 'rb'))

# Convert 'title' to a NumPy array to use in the dropdown
movie_titles = movies_list['title'].values


st.set_page_config(layout="wide", page_icon='🍿', page_title='RecommendationSystem',)

@st.cache_data
def get_image_as_base64(file):
    with open(file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

img = get_image_as_base64('movie_image.jpg')

st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"]{{
    background-image: url("data:image/png;base64,{img}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    box-shadow: inset 0 0 0 2000px rgba(0, 0, 0, 0.75); /* Adds a shadow effect */
    }}
    </style>
""", unsafe_allow_html=True)
    

st.markdown("""<h1 id="title-h"><span data-id="s1" class="spans">Movie</span><span data-id="s2">- Foresight</span></h1>""",
            unsafe_allow_html=True)

with open("title.css") as file:
    st.markdown(f'<style>{file.read()}</style>', unsafe_allow_html=True)
with open("style.css") as file:
    st.markdown(f'<style>{file.read()}</style>', unsafe_allow_html=True)


def fetch_review(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}/reviews?api_key=c5730abcfbf7a42932a4a14f1da26c12&language=en-US'
    response = requests.get(url)
    data = response.json()

    all_review = []

    for review_data in data.get('results', []):
        review = review_data.get('content', '')
        rating = review_data.get('author_details', {}).get('rating', 0)
        author = review_data.get('author', 'Unknown')

        # Check if rating is None or not provided, and set default value (e.g., 0)
        rating = rating if rating is not None else 0
        
        # Define sentiment based on the rating
        sentiment = 1 if rating >= 7 else 0
        
        all_review.append([author, review, rating, sentiment])

    # Create DataFrame with the review, rating, and sentiment
    df = pd.DataFrame(all_review, columns=['author', 'review', 'rating', 'sentiment'])

    # Function to clean HTML tags
    def clean_html(text):
        text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
        text = text.replace('\r\n', ' ')  # Replace unwanted substrings
        return text.strip()  # Remove leading/trailing spaces

    def convert_lower(text):
        return text.lower()

    def remove_special(text):
        return ''.join(char if char.isalnum() or char.isspace() else ' ' for char in text)

    # Apply text cleaning functions
    df['review'] = df['review'].apply(lambda x: remove_special(convert_lower(clean_html(x))))

    # Separate good and bad reviews
    good_review = []
    bad_review = []

    for _, row in df.iterrows():
        formatted_review = f"{row['author']} by:\n{row['review']}".replace("\n", "<br>")  # Format with author and review on separate lines
        if row['rating'] and row['rating'] >= 7:
            good_review.append(formatted_review)
        else:
            bad_review.append(formatted_review)

    return good_review, bad_review


def fetch_poster(movie_id):
    response=requests.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=c5730abcfbf7a42932a4a14f1da26c12&&language=en-US')
    data=response.json()
    # st.text(data)
    # st.text(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=c5730abcfbf7a42932a4a14f1da26c12&&language=en-US')
    return "http://image.tmdb.org/t/p/w500/"+data['poster_path']



def recommend(movie):
    # Find the index of the selected movie
    movie_index = movies_list[movies_list['title'] == movie].index[0]
    
    # Get the similarity distances for the selected movie
    distances = similarity[movie_index]
    
    # Sort movies by similarity score and exclude the first movie (which is itself)
    similar_movies = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movie_poster=[]
    recommended_movies_id=[]
    for i in similar_movies:
        movies_id=movies_list.iloc[i[0]].movie_id
        recommended_movies_id.append(movies_id)
        # Append the movie titles to the recommendation list
        recommended_movies.append(movies_list.iloc[i[0]].title)
        #  fetch poster from api
        recommended_movie_poster.append(fetch_poster(movies_id))
    #     # fetch review
    #     good_review,bad_review=fetch_review(movies_id)
    #     st.write(movies_id)
    # st.write(good_review)
    return recommended_movies,recommended_movie_poster,recommended_movies_id

# st.title("Movie Recommender System")

st.markdown("""<h1>Choose a movie name</h1>""",unsafe_allow_html=True)
# Dropdown to select a movie
selected_movie_name = st.selectbox(
    "Search",
    movie_titles
)

selected_movie_id = movies_list[movies_list['title'] == selected_movie_name]['movie_id'].values[0]
# st.text(f"Movie ID: {selected_movie_id}")

selected_movie_good_review,selected_movie_bad_review=fetch_review(selected_movie_id)

if st.button("Good Review"):
    for review in selected_movie_good_review:
        st.markdown(review,unsafe_allow_html=True)

if st.button("Bad Review"):
    for review in selected_movie_bad_review:
        st.markdown(review,unsafe_allow_html=True)

# Function to generate a Netflix search URL using the movie title
def generate_netflix_search_url(movie_title):
    # Create a URL for searching the movie on Netflix
    base_url = "https://www.netflix.com/search?q="
    search_url = base_url + movie_title.replace(" ", "%20")  # Replace spaces with '%20' for URL encoding
    return search_url

# When the 'Recommend' button is clicked, display the recommendations
if st.button('Recommend'):
    name, poster, recommended_movie_id = recommend(selected_movie_name)
    
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.text(name[0])
        # Create a clickable link for the movie poster
        netflix_url = generate_netflix_search_url(name[0])
        st.markdown(f'<a href="{netflix_url}" target="_blank"><img src="{poster[0]}" width="150"/></a>', unsafe_allow_html=True)

    with col2:
        st.text(name[1])
        netflix_url = generate_netflix_search_url(name[1])
        st.markdown(f'<a href="{netflix_url}" target="_blank"><img src="{poster[1]}" width="150"/></a>', unsafe_allow_html=True)

    with col3:
        st.text(name[2])
        netflix_url = generate_netflix_search_url(name[2])
        st.markdown(f'<a href="{netflix_url}" target="_blank"><img src="{poster[2]}" width="150"/></a>', unsafe_allow_html=True)

    with col4:
        st.text(name[3])
        netflix_url = generate_netflix_search_url(name[3])
        st.markdown(f'<a href="{netflix_url}" target="_blank"><img src="{poster[3]}" width="150"/></a>', unsafe_allow_html=True)

    with col5:
        st.text(name[4])
        netflix_url = generate_netflix_search_url(name[4])
        st.markdown(f'<a href="{netflix_url}" target="_blank"><img src="{poster[4]}" width="150"/></a>', unsafe_allow_html=True)

# st.text(selected_movie_name)
# When the 'Recommend' button is clicked, display the recommendations
# if st.button('Recommend'):
#     name,poster,recommended_movie_id = recommend(selected_movie_name)
#     # st.write(recommended_movie_id)
#     # st.write(name)

#     col1, col2, col3,col4,col5 = st.columns(5)

#     with col1:
#         st.text(name[0])
#         st.image(poster[0])
#         if st.button(poster[0]):
#             st.
#         good_review, bad_review = fetch_review(recommended_movie_id[0])
#         # if st.button('Good'):
#         #     st.text('Good Review')
#         #     for i in good_review:
#         #         st.write(i)
#         # if st.button("Bad "):
#         #     st.text('Bad Review')
#         #     for i in bad_review:
#         #         st.write(i)

#     with col2:
#         st.text(name[1])
#         st.image(poster[1])
#         good_review, bad_review = fetch_review(recommended_movie_id[1])
#         # if st.button('Good Review'):
#         #     st.text('Good Review')
#         #     for i in good_review:
#         #         st.write(i)
#         # if st.button("Bad Review"):
#         #     st.text('Bad Review')
#         #     for i in bad_review:
#         #         st.write(i)


#     with col3:
#         st.text(name[2])
#         st.image(poster[2])
#         good_review, bad_review = fetch_review(recommended_movie_id[2])
#         # if st.button('Good Review'):
#         #     st.text('Good Review')
#         #     for i in good_review:
#         #         st.write(i)
#         # if st.button("Bad Review"):
#         #     st.text('Bad Review')
#         #     for i in bad_review:
#         #         st.write(i)


#     with col4:
#         st.text(name[3])
#         st.image(poster[3])
#         good_review, bad_review = fetch_review(recommended_movie_id[3])
#         # if st.button('Good Review'):
#         #     st.text('Good Review')
#         #     for i in good_review:
#         #         st.write(i)
#         # if st.button("Bad Review"):
#         #     st.text('Bad Review')
#         #     for i in bad_review:
#         #         st.write(i)

#     with col5:
#         st.text(name[4])
#         st.image(poster[4])
#         good_review, bad_review = fetch_review(recommended_movie_id[4])
#         # if st.button('Good Review'):
#         #     st.text('Good Review')
#         #     for i in good_review:
#         #         st.write(i)
#         # if st.button("Bad Review"):
#         #     st.text('Bad Review')
#         #     for i in bad_review:
#         #         st.write(i)
