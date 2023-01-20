I want to refractor this code into class
how can I check if dataframe is empty and raise error during

def prep_batch(
    df: pd.DataFrame,
    news_domains: list,
    remove_news=True,
    print_out=True,
    **kwargs,
) -> pd.DataFrame:
    """Loads tweets from database. Applies transformation to them:
    removes retweets, finds and remove tweets with links to news site

    Args:
        df (pd.DataFrame): input DataFrame
        news_domains (list): list containing news sites domains
        remove_news (bool, optional):
            If you want to remove news from feed. Defaults to "True"
        kwargs:
            mute_list (list, optional):
                list of words, to remove additional tweets. Defaults to None.
            mute_list_cs (list, optional):
                case-sensitive list of words, as above. Defaults to None.
            data_path (str, optional):
                Path to folder with "seen.csv". Defaults to "tweetfeed/data/".

    Returns:
        pd.DataFrame: filtered DataFrame with 2 columns, "id" and "user".
    """
    # TODO make this into class
    if df.empty:
        raise ValueError("ValueError: DataFrame is empty, nothing to add")

    # remove retweets
    # TODO this should be options
    df = df[df["lang"] == "en"]  # take only english lang tweets

    if_empty_df_raise(
        df,
        to_print="ValueError:After removing non-english tweets, DataFrame is empty, nothing to add",
    )
    df = df[df["retweeted_status"] == "N/A"]  # remove RT
    if_empty_df_raise(
        df,
        to_print="ValueError:After removing RT, DataFrame is empty, nothing to add",
    )
    # TODO change this into function
    if "data_path" in kwargs:
        d_path = kwargs["data_path"]
        df = rem_seen_tweets(df, d_path)
        if_empty_df_raise(
            df,
            to_print="after removing seen, DataFrame is empty, nothing to add",
        )
        # if there are predictions, add them to df
        try:
            predictions = pd.read_csv(f"{d_path}/predictions.csv")
            try:
                df.insert(
                    3,
                    "preds",
                    df["id"].map(
                        predictions.set_index("id")["predicted"],
                        na_action="ignore",
                    ),
                )
                df["preds"] = df["preds"].fillna(0)
                df.sort_values(by="preds", ascending=False, inplace=True)
            except pd.errors.InvalidIndexError:
                print("duplicate values in predictions.csv, resetting scores")
                df["preds"] = 0
        except FileNotFoundError:
            print("no predictions file loaded")
            df["preds"] = 0
    else:
        df["preds"] = 0

    if "likes" in kwargs:
        if kwargs["likes"] > 0:
            df = rem_on_likes(df, likes=kwargs["likes"])
    # filter out tweets with news links
    # mark tweets as news
    df = find_news(df, news_domains)  # add news column
    # TODO remove batch size, don't need it
    if "batch_size" in kwargs:
        batch_size = kwargs["batch_size"]
    else:
        batch_size = df.shape[0]
    if remove_news:
        to_custom_news_feed = (
            df[df["contains_news"] == 0]
            # .sample(frac=1)
            .reset_index(drop=True)[:batch_size]
        )

    if remove_news is False:
        to_custom_news_feed = (
            df
            # .sample(frac=1)
            .reset_index(drop=True)[:batch_size]
        )
    if_empty_df_raise(
        to_custom_news_feed,
        to_print="after removing tweets containing news, DataFrame is empty, nothing to add",
    )
    # TODO drop tweets from ME
    # TODO create test mute lists

    if "mute_list" in kwargs:
        to_custom_news_feed = drop_contains(
            to_custom_news_feed,
            column_name="full_text",
            str_list=kwargs["mute_list"],
        )
    if "mute_list_cs" in kwargs:
        to_custom_news_feed = drop_contains(
            to_custom_news_feed,
            column_name="full_text",
            str_list=kwargs["mute_list_cs"],
            case_sensitive=True,
        )
    # concat tweet with in_reply, quoted tweets
    df = concat_tweet_text(df)

    df = to_custom_news_feed[["id", "user", "full_text", "preds"]]
    # TODO filter out user own tweets
    print(f"{df.shape[0]} tweets in a batch")
    if_empty_df_raise(
        to_custom_news_feed,
        to_print="after removing tweets containing muted words, DataFrame is empty, nothing to add",
    )
    if print_out:
        print("top prediction scores from batch: ")
    top_pred_list = list(df["preds"].nlargest(n=3))
    print("3 top prediction scores from batch:")
    for score in top_pred_list:
        print(score)
    # df.sort_values(by=["preds"], ascending=False, inplace=True)
    # TODO sort preds from highest
    return df






    ----

I have refractored it. I just want to check if df is empty during process_tweet, after each function call
    class TweetProcessor:
    def __init__(self, df: pd.DataFrame, news_domains: list, remove_news=True, **kwargs):
        self.df = df
        self.news_domains = news_domains
        self.remove_news = remove_news
        self.kwargs = kwargs

        """Loads tweets from database. Applies transformation to them:
        removes retweets, finds and remove tweets with links to news site

        Args:
            df (pd.DataFrame): input DataFrame
            news_domains (list): list containing news sites domains
            remove_news (bool, optional):
                If you want to remove news from feed. Defaults to "True"
            kwargs:
                mute_list (list, optional):
                    list of words, to remove additional tweets. Defaults to None.
                mute_list_cs (list, optional):
                    case-sensitive list of words, as above. Defaults to None.
                data_path (str, optional):
                    Path to folder with "seen.csv". Defaults to "tweetfeed/data/".

        Returns:
            pd.DataFrame: filtered DataFrame with 2 columns, "id" and "user".
        """
        
    def remove_retweets(self):
        self.df = self.df[self.df["retweeted_status"] == "N/A"]

    def select_lang(self, lang="en"):
        self.df = self.df[self.df["lang"] == lang]
        
    def remove_seen_tweets(self):
        if "data_path" in self.kwargs:
            d_path = self.kwargs["data_path"]
            self.df = rem_seen_tweets(self.df, d_path)
        
    def add_predictions(self):
        if "data_path" in self.kwargs:
            d_path = self.kwargs["data_path"]
            try:
                predictions = pd.read_csv(f"{d_path}/predictions.csv")
                try:
                    self.df.insert(
                        3,
                        "preds",
                        self.df["id"].map(
                            predictions.set_index("id")["predicted"],
                            na_action="ignore",
                        ),
                    )
                    self.df["preds"] = self.df["preds"].fillna(0)
                    self.df.sort_values(by="preds", ascending=False, inplace=True)
                except pd.errors.InvalidIndexError:
                    print("duplicate values in predictions.csv, resetting scores")
                    self.df["preds"] = 0
            except FileNotFoundError:
                print("no predictions file loaded")
                self.df["preds"] = 0
        else:
            self.df["preds"] = 0
            
    def filter_on_likes(self):
        if "likes" in self.kwargs:
            if self.kwargs["likes"] > 0:
                self.df = rem_on_likes(self.df, likes=self.kwargs["likes"])
                
    def filter_news(self):
        self.df = find_news(self.df, self.news_domains)
        if self.remove_news:
            self.df = self.df[self.df["contains_news"] == 0].reset_index(drop=True)[:self.batch_size]
        else:
            self.df = self.df.reset_index(drop=True)[:self.batch_size]

    def remove_from_mutelist(self):
        if "mute_list" in self.kwargs:
            self.df = drop_contains(self.df, "full_text", self.kwargs["mute_list"])
        if "mute_list_cs" in self.kwargs:
            self.df = drop_contains(self.df, "full_text", self.kwargs["mute_list_cs"], case_sensitive=True)
        
    def process_tweets(self):
        self.remove_retweets()
        self.select_lang()
        self.remove_seen_tweets()
        self.remove_from_mutelist()
        self.add_predictions()
        self.filter_on_likes()
        self.filter_news()
        