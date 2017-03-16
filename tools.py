import numpy as np
import nltk
import igraph
import csv
import pandas as pd
from collections import defaultdict
from itertools import combinations
from sklearn.metrics import f1_score

stpwds = set(nltk.corpus.stopwords.words("english"))
stemmer = nltk.stem.PorterStemmer()


def articles_graph(path=""):
    with open(path + "data/training_set.txt", "r") as f:
        reader = csv.reader(f)
        training_set = list(reader)
    training_set = [element[0].split(" ") for element in training_set]
    node_id_df = pd.read_csv("data/node_information.csv", header=None, usecols=[0]).values.reshape(-1)

    g = igraph.Graph(directed=True)

    g["articles_to_index"] = dict(zip(node_id_df, range(len(node_id_df))))
    g.add_vertices([i for i in range(len(node_id_df))])
    edges = []
    for element in training_set:
        if element[2] == "1":
            edges.append((g["articles_to_index"][int(element[0])], g["articles_to_index"][int(element[1])]))
    g.add_edges(edges)
    return g


def authors_citation_dict(path=""):
    with open(path + "data/training_set.txt", "r") as f:
        reader = csv.reader(f)
        training_set = list(reader)

    training_set = [element[0].split(" ") for element in training_set]
    node_information_df = pd.read_csv("data/node_information.csv", header=None)

    node_information_df.columns = ["ID", "year", "title", "authors", "journalName", "abstract"]
    node_information_df = node_information_df.reset_index().set_index("ID")
    node_information_df["authors"].fillna("", inplace=True)
    authors = node_information_df["authors"].values.tolist()
    authors = [author_list.split(", ") for author_list in authors]
    authors = [list(filter(None, author_list)) for author_list in authors]

    id_to_index = dict(zip(node_information_df.index.values, range(node_information_df.index.size)))

    dict_edges = defaultdict(int)
    for element in training_set:
        if element[2] == "1":
            for author_source in authors[id_to_index[int(element[0])]]:
                for author_target in authors[id_to_index[int(element[1])]]:
                    dict_edges[(author_source, author_target)] += 1

    return dict_edges


def authors_citation_graph(path=""):
    with open(path + "data/training_set.txt", "r") as f:
        reader = csv.reader(f)
        training_set = list(reader)

    training_set = [element[0].split(" ") for element in training_set]
    node_information_df = pd.read_csv("data/node_information.csv", header=None)

    node_information_df.columns = ["ID", "year", "title", "authors", "journalName", "abstract"]
    node_information_df = node_information_df.reset_index().set_index("ID")
    node_information_df["authors"].fillna("", inplace=True)
    authors = node_information_df["authors"].values.tolist()
    authors = [author_list.split(", ") for author_list in authors]
    authors = [list(filter(None, author_list)) for author_list in authors]
    concatenated_authors = np.concatenate(tuple(authors))
    unique_authors = list(set(concatenated_authors))

    g = igraph.Graph(directed=True)
    g.add_vertices([i for i in range(len(unique_authors))])
    g.vs["weight"] = np.zeros(len(unique_authors))
    g["authors_to_index"] = dict(zip(unique_authors, range(len(unique_authors))))

    id_to_index = dict(zip(node_information_df.index.values, range(node_information_df.index.size)))

    edges = []
    for element in training_set:
        if element[2] == "1":
            for author_source in authors[id_to_index[int(element[0])]]:
                for author_target in authors[id_to_index[int(element[1])]]:
                    if (author_source != author_target):
                        edges.append((g["authors_to_index"][author_source], g["authors_to_index"][author_target]))
                    else:
                        g.vs[g["authors_to_index"][author_source]]["weight"] += 1

    g.add_edges(edges)
    g.es["weight"] = np.ones(len(edges))
    g = g.simplify(combine_edges='sum')
    return g


def authors_collaboration_graph():
    node_information_df = pd.read_csv("data/node_information.csv", header=None)

    node_information_df.columns = ["ID", "year", "title", "authors", "journalName", "abstract"]
    node_information_df = node_information_df.reset_index().set_index("ID")
    node_information_df["authors"].fillna("", inplace=True)
    authors = node_information_df["authors"].values.tolist()
    authors = [author_list.split(", ") for author_list in authors]
    authors = [list(filter(None, author_list)) for author_list in authors]
    concatenated_authors = np.concatenate(tuple(authors))
    unique_authors = list(set(concatenated_authors))

    g = igraph.Graph(directed=False)
    g.add_vertices([i for i in range(len(unique_authors))])
    g["authors_to_index"] = dict(zip(unique_authors, range(len(unique_authors))))
    authors_list_ids = [[g["authors_to_index"][author] for author in author_list] for author_list in authors]
    edges = []
    for author_list_id in authors_list_ids:
        edges += list(combinations(author_list_id, 2))

    g.add_edges(edges)
    g.es["weight"] = np.ones(len(edges))
    g = g.simplify(combine_edges='sum')
    return g


def remove_stopwords_and_stem(words):
    words = [token for token in words if (len(token) > 2 and (token not in stpwds))]
    return [stemmer.stem(token) for token in words]


def random_sample(df, p=0.05, seed=42):
    '''
    Randomly samples a proportion 'p' of rows of a dataframe
    '''
    size = df.shape[0]
    np.random.seed(seed)
    return df.ix[np.random.randint(0, size, int(size * p)), :]


def stats_df(df):
    '''
    Gives stats about the dataframe
    '''
    print("Nb lines in the train : ", len(df["from"]))
    print("Nb of unique nodes : ", len(df["from"].unique()))
    print("The document that cites the most, cites : ", df.groupby(["from"]).sum()["y"].max(), " document(s).")
    print("The document with no citation : ", sum(df.groupby(["from"]).sum()["y"] == 0), "\n")
    print("The most cited document, is cited : ", df.groupby(["to"]).sum()["y"].max(), " times.")
    print("Nb of documents never cited  : ", sum(df.groupby(["to"]).sum()["y"] == 0), "\n")
    print("There are NaN to handle for authors and journalName :")


def xgb_f1(y, t):
    '''
    :param y: true labels
    :param t: predicted labels
    :return: f1 score
    '''
    # t = t.get_label()
    y_bin = [1. if y_cont > 0.5 else 0. for y_cont in y]  # binaryzing your output
    return 'f1', f1_score(t, y_bin)
