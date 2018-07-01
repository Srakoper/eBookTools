"""
Use for modifying filenames of books and comparing filenames within directory or between directories.
See function docstrings for explanation of function behavior and logic.
"""

import os
from shutil import copy2
import re
import difflib
from random import choice as ch
from zipfile import ZipFile as ZF
import sqlite3
from datetime import datetime
from time import time

### FUNCTIONS ###

def getPath():
    """
    Returns path to directory with book filenames entered as input from user.
    :return: path to directory with book filenames
    """
    path = input("\nEnter path to directory with books: ")
    if path[-1] != "\\": path = path + "\\"
    return path

def getBooks(path):
    """
    Gets a list of book filenames from a given path.
    Valid extensions: .pdf, .azw, .epub, .mobi
    :param path: full path to a directory with files searched for book filenames
    :return: list of all book filenames from path
    """
    books = os.listdir(path)
    for book in books[:]:
        if not (re.search(r".pdf$", book)\
                or re.search(r".azw$", book)\
                or re.search(r".epub$", book)\
                or re.search(r".mobi$", book)): books.remove(book)
    return books

def sortBooks(path, books):
    """
    Sorts book filenames by author, title (without articles), date modified or size descending
    and return a list of sorted books.
    :param path: full path to a directory with files to be modified
    :param books: list of filenames to sort
    :return: sorted list of book filenames
    """
    while True:
        sorting = input("\nSort by author (A), title (T), date modified (D) or size descending (S)? A/N/D/S ")
        if sorting.lower() in ["a", "t", "d", "s"]: break
        else: print("\nEnter a valid choice.\n")
    if sorting.lower() == "a": return sorted(books, key=lambda s: s.lower()), "by author", None
    elif sorting.lower() == "t":
        by_title = list()
        sorted_by_title = list()
        for book in books:
            title = re.sub(r".+\s-\s", "", book)
            if title.split()[0] in ("A", "An", "The", "El", "La", "Los", "Las", "Un", "Una",
                                                           "Unos", "Unas", "Le", "L'", "Les", "Une", "Des", "Der",
                                                           "Die", "Das", "Ein", "Eine"):
                by_title.append((re.sub(r"^\w+\s", "", title), book))
            else: by_title.append((title, book))
        for book in sorted(by_title, key=lambda s: s[0].lower()): sorted_by_title.append(book[1])
        return sorted_by_title, "by title", None
    elif sorting.lower() == "d":
        by_date = list()
        dates = list()
        sorted_by_date = list()
        for book in books: by_date.append((str(datetime.fromtimestamp(int(os.stat(path + book).st_mtime))), book))
        for book in sorted(by_date, reverse=True):
            dates.append(book[0])
            sorted_by_date.append(book[1])
        return sorted_by_date, "by date modified", dates
    else:
        by_size = list()
        sizes = list()
        sorted_by_size = list()
        for book in books: by_size.append((int(os.stat(path + book).st_size), book))
        for book in sorted(by_size, reverse=True):
            sizes.append(str(book[0]) + " bytes")
            sorted_by_size.append(book[1])
        return sorted_by_size, "by size", sizes

def selectBooks():
    """
    Selects individual books from a list of sorted book filenames and returns a list of selected books.
    !!! Inputs for selection must be valid numbers from a list of sorted book filenames. !!!
    Inputs can be individual numbers, ranges in format [from]-[to] (inclusive),
    or a combination of both, separated by commas, e.g.:
        select one individual: 1
        select multiple individual: 1,2,5,10
        select range: 50-100
        select multiple ranges: 50-100,200-250
        select multiple individual and ranges: 1,5,10-20,50,55-65
    :return: list of selected book filenames
    """
    sorted_books, sorted_by, details = sortBooks(path, books)
    print("\nBooks sorted {}:\n".format(sorted_by))
    if details:
        counter = 0
        for book in enumerate(sorted_books, start=1):
            if len(book[1]) >= 60: print("{:>4} {:<60} {:>19}".format(book[0], book[1][:54] + "...", details[counter]))
            else: print("{:>4} {:<60} {:>19}".format(book[0], book[1], details[counter]))
            #print(book[0], book[1], details[0])
            counter += 1
    else:
        for book in enumerate(sorted_books, start=1): print(book[0], book[1])
    while True:
        try:
            selected = input("\nSelect books by individual numbers or ranges (from-to), separated by commas: ")
            selections = selected.replace(" ", "").split(",")
            numbers = set()
            selected_books = list()
            for selection in selections:
                if "-" in selection:
                    for i in range(int(selection.split("-")[0]) - 1, int(selection.split("-")[1])): numbers.add(i)
                else: numbers.add(int(selection) - 1)
            for number in numbers: selected_books.append(sorted_books[number])
            print("\nSelected books ({}):\n".format(len(selected_books)))
            for book in enumerate(selected_books, start=1): print("{:>4} {}".format(book[0], book[1]))
            return selected_books
        except: print("\nIncorrect input for selected books. Enter a valid input.")

def removeMultipleSpacing(path, books, undo):
    """
    Removes multiple (>= 2) spacing and spacing at the end of filename from filename and replaces with single space.
    Stores new and old filenames to undo dictionary allowing restoration of modified filenames via undo method.
    :param path: full path to a directory with files to be modified
    :param books: list of filenames to remove multiple spacing from
    """
    undo.clear()
    counter = 0
    for book in books:
        old = book
        spacing = False
        if ".epub" in book.lower() or ".mobi" in book.lower():
            while True:
                if book[-6] == " ":
                    book = book[:-6] + book[-5:]
                    spacing = True
                else: break
        elif ".pdf" in book.lower():
            while True:
                if book[-5] == " ":
                    book = book[:-5] + book[-4:]
                    spacing = True
                else: break
        if re.search(r"\s{2,}", book):
            book = re.sub(r"\s{2,}", " ", book)
            os.rename(path + old, path + book)
            spacing = True
        if spacing:
            undo[book] = old
            counter +=1
            print("Multiple and/or end spacing removed from filename: {}; new filename: {}".format(path + old, book))
    print("\nProcess finished. Multiple spacing removed from {} filenames.".format(str(counter)))

def fixCommaSpacing(path, books, undo):
    """
    Fixes commas preceded by spacing ([char] ,) or not followed by spacing (,[char]) to appropriate form ([char], )
    !!! Ignores comma between numbers (e.g. 10,000). !!!
    !!! Removing multiple spacing prior to and/or after fixing commas is recommended. !!!
    Stores new and old filenames to undo dictionary allowing restoration of modified filenames via undo method.
    :param path: full path to a directory with files to be modified
    :param books: list of filenames to fix comma spacing in
    """
    undo.clear()
    counter = 0
    for book in books:
        old = book
        changed = False
        if re.search(r"(\s,)", book):
            book = re.sub(r"\s,", ",", book)
            os.rename(path + old, path + book)
            changed = True
        if re.search(r",\S", book) and not re.search(r",\d", book):
            book = re.sub(r",", ", ", book)
            os.rename(path + old, path + book)
            changed = True
        if changed:
            undo[book] = old
            counter += 1
            print("Comma spacing fixed in filename: {}; new filename: {}".format(path + old, book))
    print("\nProcess finished. Comma spacing fixed in {} filenames.".format(str(counter)))

def fixApostrophes(path, books, undo):
    """
    Replaces all instances of [letter]_[letter] with [letter]'[letter].
    Stores new and old filenames to undo dictionary allowing restoration of modified filenames via undo method.
    :param path: full path to a directory with files to be modified
    :param books: list of filenames to fix apostrophes in
    """
    undo.clear()
    counter = 0
    for book in books:
        if re.search(r"[A-Za-z]_[A-Za-z]", book):
            old = book
            book = re.sub(r"(?<=[A-Za-z])_(?=[A-Za-z])", "'", book)
            os.rename(path + old, path + book)
            counter += 1
            undo[book] = old
            print(old, "changed to", book)
    print("\nProcess finished. Apostrophes fixed in {} filenames.".format(str(counter)))

def findHypenWithoutSpacing(path, books):
    """
    Finds hyphen (-) char not preceded or followed by spacing.
    !!! Does not modify filename because hyphen without spacing can be a legitimate part of names or word associations. !!!
        legitimate use: "Saint-Exupéry, Antoine de ..."
        illegitimate use: "Clarke, Arthur-2001 ..."
    :param path: full path to a directory with files to be searched
    :param books: list of filenames to find hyphen without spacing in
    """
    counter = 0
    for book in books:
        if re.search(r"(\.epub)|(\.mobi)", book) and re.search(r"(\S-\S)|(\S-\s)|(\s-\S)", book):
            counter += 1
            print("Hyphen without spacing found in filename: {}".format(path + book))
    print("\nProcess finished. Hyphen without spacing found in {} filenames.".format(str(counter)))

def findNoAuthorFirst(path, books):
    """
    Finds possible filenames not starting with author(s), i.e. of the "<author(s)> - <title[_ subtitle]>" format;
    "<author(s)>" being of the "<Surname [Other_surname...], Name [Other_name...]>" format.
    !!! Does not modify filename. !!!
    :param path: full path to a directory with files to be searched
    :param books: list of filenames to find missing authors at the start in
    """
    counter = 0
    for book in books:
        if re.search(r"(\.epub)|(\.mobi)", book) and not re.search(r".+,.+-", book):
            counter += 1
            print("Possible missing author at the start found in filename: {}".format(path + book))
    print("\nProcess finished. Possible missing authors found in {} filenames.".format(str(counter)))

def findMissingCapitalization(path, books):
    """
    Finds missing capitalization of authors and words.
    Missing capitalization == True iff:
        first char in word is lowercase AND
        word not a, an, and, as, at, by, das, de, degli, dei, del, dell, della, delle, delli, dello, der, des, du, ed,
        ein, eine, el, for, from, il, in, into, le, la, las, les, los, nor, of, on, onto, or, the, to, tr, un, una, une,
        unto, uno, unas, unos, ur van, von, with
    !!! Does not modify filename. !!!
    !!! Will find missing capitalization in titles of non-English books that follow different capitalization rules. !!!
    :param path: full path to a directory with files to be searched
    :param books: list of filenames to find missing capitalization in
    """
    counter = 0
    for book in books:
        if re.search(r"(\.epub)|(\.mobi)", book):
            noncapitalized = False
            for word in re.sub(r"[,\-!'_()]", "", book[:-5]).split():
                if word not in ("a", "an", "and", "as", "at", "by", "das", "de", "degli", "dei", "del", "dell", "della",
                                "delle", "delli", "dello", "der", "des", "du", "ed.", "ein", "eine", "el", "for",
                                "from", "il", "in", "into", "la", "las", "le", "les", "los", "nor", "of", "on", "onto",
                                "or", "the", "to", "tr.", "un", "una", "une", "uno", "unto", "unas", "unos", "ur.",
                                "van", "von", "with") and word[0].islower():
                    noncapitalized = True
                    print("Possible missing capitalization in word: '{}' in filename: {}".format(word, path + book))
            if noncapitalized: counter += 1
    print("\nProcess finished. Possible missing capitalization found in {} filenames.".format(str(counter)))

def findSubtitles(books):
    """
    Finds possible subtitles in book filenames (containing '_' indicating the presence of a subtitle).
    Lists books containing possible subtitles.
    :param books: list of filenames to be checked for possible subtitles
    """
    counter = 0
    for book in books:
        if re.search(r"\.epub", book.lower())\
                or re.search(r"\.mobi", book.lower())\
                or re.search(r"\.pdf", book.lower()):
            if "_" in book:
                counter += 1
                print("Possible subtitle found in book {}".format(book))
    print("\nProcess finished. Possible subtitles found in {} filenames.".format(str(counter)))

def withoutAuthors(path, books, undo):
    """
    Requires filename to be in "<author(s)> - <title[_ subtitle]>" format with any extension.
    Crops author(s) and subtitle(s) from filename: "<author(s)> - <title[_ subtitle[, A/An/The]]>.extension" -> "<[A/An/The ]title>.extension"
    Stores new and old filenames to undo dictionary allowing restoration of modified filenames via undo method.
    :param path: full path to a directory with files to be modified
    :param books: list of filenames to be modified
    """
    undo.clear()
    pattern1 = re.compile(r".+?\s-\s") # finds author(s)
    pattern2 = re.compile(r"_+\s.+(?=\.)") # finds a subtitle of a book
    for book in books:
        old = book
        os.rename(path + book, path + re.sub(pattern1, "", book, 1))
        noauthor = re.sub(pattern1, "", book, 1)
        if re.search(r".+(, A)\.", noauthor[-9:]):
            os.rename(path + noauthor, path + "A " + re.sub(pattern2, "", re.sub(",\sA\.", ".", noauthor), 1))
            new = "A " + re.sub(pattern2, "", re.sub(",\sA\.", ".", noauthor), 1)
        elif re.search(r".+(, An)\.", noauthor[-10:]):
            os.rename(path + noauthor, path + "An " + re.sub(pattern2, "", re.sub(",\sAn\.", ".", noauthor), 1))
            new = "An " + re.sub(pattern2, "", re.sub(",\sAn\.", ".", noauthor), 1)
        elif re.search(r".+(, The)\.", noauthor[-11:]):
            os.rename(path + noauthor, path + "The " + re.sub(pattern2, "", re.sub(",\sThe\.", ".", noauthor), 1))
            new = "The " + re.sub(pattern2, "", re.sub(",\sThe\.", ".", noauthor), 1)
        else:
            os.rename(path + noauthor, path + re.sub(pattern2, "", noauthor, 1))
            new = re.sub(pattern2, "", noauthor, 1)
        if new[-1] == "_":
            os.rename(path + new, path + new[:-1])
            new = new[:-1]
        undo[new] = old
        print(old, "changed to", new)

def withAuthors(path, books, undo):
    """
    Requires filename to be in "<author(s)> - <title[_ subtitle]>" format with any extension.
    Crops subtitle(s) from filename: "<author(s)> - <title[_ subtitle[, <article>]]>.extension" -> "<author(s)> - <[<article> <title>.extension"
    Stores new and old filenames to undo dictionary allowing restoration of modified filenames via undo method.
    :param path: full path to a directory with files to be modified
    :param books: list of filenames to be modified
    """
    undo.clear()
    to_rename = dict()
    pattern = re.compile(r"_+\s.+(?=\.)") # finds a subtitle of a book
    for book in books:
        if ".kepub" in book:
            old = book
            to_rename[old] = renameBook(book.replace(".kepub", ""), pattern).replace(".epub", ".kepub.epub")
        else:
            old = book
            to_rename[old] = renameBook(book, pattern)
    for old, new in to_rename.items():
        if new[-1] == "_":
            undo[new[:-1]] = old
            os.rename(path + old, path + new[:-1])
            print(old, "changed to", new[:-1])
        else:
            undo[new] = old
            try:
                os.rename(path + old, path + new)
                print(old, "changed to", new)
            except FileExistsError: # prevents termination if multiple books would be renamed to a same new filename
                while True:
                    exists = input("\nFile with proposed name {} already exists. Press N to enter a new filename or O to revert to old filename {}: ".format(new, old))
                    if exists in ["n", "N", "o", "O"]: break
                if exists in ["n", "N"]:
                    new = input("\nEnter a new filename: ")
                    undo[new] = old
                    os.rename(path + old, path + new)
                    print("\n" + old, "changed to", new + "\n")
                else: print("\nFile with name {} not renamed.\n".format(old))
    print("\nProcess finished. {} filenames renamed with subtitles removed and authors retained.".format(len(to_rename)))

def renameBook(book, pattern):
    """
    Helper function for renaming books within function withAuthors.
    :param book: book to be renamed
    :param pattern: regex pattern for finding subtitle
    :return: string of a renamed book
    """
    # English
    if re.search(r".+(, A)\.", book[-9:]): return re.sub("\s-\s", " - A ", re.sub(pattern, "", re.sub(",\sA\.", ".", book), 1), 1)
    elif re.search(r".+(, An)\.", book[-10:]): return re.sub("\s-\s", " - An ", re.sub(pattern, "", re.sub(",\sAn\.", ".", book), 1), 1)
    elif re.search(r".+(, The)\.", book[-11:]): return re.sub("\s-\s", " - The ", re.sub(pattern, "", re.sub(",\sThe\.", ".", book), 1), 1)
    # Spanish
    elif re.search(r".+(, El)\.", book[-10:]): return re.sub("\s-\s", " - El ", re.sub(pattern, "", re.sub(",\sEl\.", ".", book), 1), 1)
    elif re.search(r".+(, La)\.", book[-10:]): return re.sub("\s-\s", " - La ", re.sub(pattern, "", re.sub(",\sLa\.", ".", book), 1), 1)
    elif re.search(r".+(, Los)\.", book[-11:]): return re.sub("\s-\s", " - Los ", re.sub(pattern, "", re.sub(",\sLos\.", ".", book), 1), 1)
    elif re.search(r".+(, Las)\.", book[-11:]): return re.sub("\s-\s", " - Las ", re.sub(pattern, "", re.sub(",\sLas\.", ".", book), 1), 1)
    elif re.search(r".+(, Un)\.", book[-10:]): return re.sub("\s-\s", " - Un ", re.sub(pattern, "", re.sub(",\sUn\.", ".", book), 1), 1)
    elif re.search(r".+(, Una)\.", book[-11:]): return re.sub("\s-\s", " - Una ", re.sub(pattern, "", re.sub(",\sUna\.", ".", book), 1), 1)
    elif re.search(r".+(, Unos)\.", book[-12:]): return re.sub("\s-\s", " - Unos ", re.sub(pattern, "", re.sub(",\sUnos\.", ".", book), 1), 1)
    elif re.search(r".+(, Unas)\.", book[-12:]): return re.sub("\s-\s", " - Unas ", re.sub(pattern, "", re.sub(",\sUnas\.", ".", book), 1), 1)
    # French ("La", "Un" covered previously)
    elif re.search(r".+(, Le)\.", book[-10:]): return re.sub("\s-\s", " - Le ", re.sub(pattern, "", re.sub(",\sLe\.", ".", book), 1), 1)
    elif re.search(r".+(, L')\.", book[-10:]): return re.sub("\s-\s", " - L' ", re.sub(pattern, "", re.sub(",\sL'\.", ".", book), 1), 1)
    elif re.search(r".+(, Les)\.", book[-11:]): return re.sub("\s-\s", " - Les ", re.sub(pattern, "", re.sub(",\sLes\.", ".", book), 1), 1)
    elif re.search(r".+(, Une)\.", book[-11:]): return re.sub("\s-\s", " - Une ", re.sub(pattern, "", re.sub(",\sUne\.", ".", book), 1), 1)
    elif re.search(r".+(, Des)\.", book[-11:]): return re.sub("\s-\s", " - Des ", re.sub(pattern, "", re.sub(",\sDes\.", ".", book), 1), 1)
    # German
    elif re.search(r".+(, Der)\.", book[-11:]): return re.sub("\s-\s", " - Der ", re.sub(pattern, "", re.sub(",\sDer\.", ".", book), 1), 1)
    elif re.search(r".+(, Die)\.", book[-11:]): return re.sub("\s-\s", " - Die ", re.sub(pattern, "", re.sub(",\sDie\.", ".", book), 1), 1)
    elif re.search(r".+(, Das)\.", book[-11:]): return re.sub("\s-\s", " - Das ", re.sub(pattern, "", re.sub(",\sDas\.", ".", book), 1), 1)
    elif re.search(r".+(, Ein)\.", book[-11:]): return re.sub("\s-\s", " - Ein ", re.sub(pattern, "", re.sub(",\sEin\.", ".", book), 1), 1)
    elif re.search(r".+(, Eine)\.", book[-12:]): return re.sub("\s-\s", " - Eine ", re.sub(pattern, "", re.sub(",\sEine\.", ".", book), 1), 1)
    # removes subtitle only
    else: return re.sub(pattern, "", book, 1)

def restoreAuthors(path, books, undo):
    """
    Restores author(s) to a filename if a filename is found in different path and contains author(s) data.
    Requires input directory of filenames w/o author(s) data and a comparison directory of filenames with author(s) data.
    Will match filenames iff title data corresponds exactly:
        "Code", "Petzold, Charles - Code" -> match
        "Code", "Deibert, Ronald - Black Code" -> no match
    !!! Assumes identified books with author(s) data are structurally equal to corresponding books w/o author(s) data, but this is not guaranteed. !!!
    !!! Complexity is O(n^2). !!!
    Stores new and old filenames to undo dictionary allowing restoration of modified filenames via undo method.
    :param path: full path to a directory with files to be modified
    :param books: list of filenames to have authors restored
    """
    undo.clear()
    path2 = input("Enter path to other directory with books to compare: ")
    books2 = os.listdir(path2)
    counter = 0
    for book1 in books:
        title1 = re.findall(r"(.+)\.", book1)
        extension1 = re.findall(r"\.(\w+)", book1)
        for book2 in books2:
            if re.search(r"\.epub", book1.lower())\
                    or re.search(r"\.mobi", book1.lower())\
                    or re.search(r"\.pdf", book1.lower()): title2 = re.findall(r"\s-\s(.+)\.", book2)
            if title2 and title1[0] == title2[0]:
                new = re.findall(r".+\.", book2)[0] + extension1[0]
                os.rename(path + book1, path + new)
                undo[new] = book1
                counter += 1
                print("{} changed to {}".format(book1, new))
                break
        print("Author(s) data not found for", book1)
    print("\nProcess finished. Author(s) data restored to {} filenames.".format(str(counter)))


def removeSubstring(path, books, undo):
    """
    Removes a given substring from all filenames that contain substring or ignores otherwise.
    !!! Only removes the first occurrence of a given substring. !!!
    Stores new and old filenames to undo dictionary allowing restoration of modified filenames via undo method.
    :param path: full path to a directory with files to be modified
    :param books: list of filenames to have substrings removed
    """
    undo.clear()
    substring = input("Enter substring to remove from filename(s): ")
    counter = 0
    for book in books:
        if substring in book:
            new = book.replace(substring, "", 1)
            os.rename(path + book, path + new)
            undo[new] = book
            counter += 1
            print("{} changed to {}".format(book, new))
        else:
            print("{} contains no substring {}".format(book, substring))
    print("\nProcess finished. Substring removed from {} filenames.".format(str(counter)))

def restoreOld(path, undo):
    """
    Restores modified filenames to form before modification.
    Requires stored new and old filenames in undo dictionary.
    To be used with removeMultipleSpacing, fixCommaSpacing, fixApostrophes, withoutAuthors, withAuthors, restoreAuthors and removeSubstring methods.
    !!! Best applied immediately after filename modification. !!!
    :param path: full path to a directory with files to be modified
    :param undo: dictionary with stored new and old filenames
    """
    counter = 0
    if not undo: print("No filenames to restore.")
    else:
        for new, old in undo.items():
            try:
                os.rename(path + new, path + old)
                counter += 1
            except FileNotFoundError: print("{} not found in {}".format(new, path))
        print("Process finished. {} filenames restored.".format(counter))

def compareTwoDirs(path, books):
    """
    Compares names without extensions of files in two directories (dir1, dir2).
    Modify index boolean to set different similarity threshold (default: index >= 0.9).
    !!! Complexity is O(|dir1|*|dir2|) and similarity ratios are slow to compute, so expect long running time for large inputs. !!!
    Prints a list of:
        identical files (except for extension) iff filenames found in both dirs
        pairs of similar files that are not identical (a filename can be similar to multiple filenames)
        files not found in dir2 (!!! similar filenames count as found !!!)
    !!! Order of dirs is important. !!!
    !!! Run with reversed dirs to find files in dir2 not found in dir1. !!!
    !!! False positives: distinct books with similar author(s) and/or title. !!!
    :param path: full path to a dir1 with files to be compared to files from dir2
    :param books: list of filenames from dir1 to be compared to filenames from dir2
    """
    path2 = input("Enter path to other directory with books to compare: ")
    books2 = os.listdir(path2)
    identical = list()
    similar = list()
    different = list()
    if path2[-1] != "\\": path2 = path2 + "\\"
    for book1 in books:
        if re.search(r"\.epub", book1.lower())\
                or re.search(r"\.mobi", book1.lower())\
                or re.search(r"\.pdf", book1.lower()): b1 = re.sub(r"\.\w+", "", book1)
        else: continue
        not_found = True
        for book2 in books2:
            if re.search(r"\.epub", book2.lower())\
                    or re.search(r"\.mobi", book2.lower())\
                    or re.search(r"\.pdf", book2.lower()):
                b2 = re.sub(r"\.\w+", "", book2)
                index = difflib.SequenceMatcher(None, b1, b2).quick_ratio()
                if index == 1:
                    identical.append(b1)
                    not_found = False
                    break
                elif index >= 0.9:
                    similar.append((b1, b2))
                    not_found = False
        if not_found: different.append(b1)
    print("\nBooks found in", path, "and", path2 + ":\n")
    if identical:
        for book in identical: print(book)
    else: print("N/A")
    print("\nBooks in", path, "similar to books in", path2 + ":\n")
    if similar:
        for pair in similar: print(str(pair)[1:-1])
    else: print("N/A")
    print("\nBooks in", path, "not found in", path2 + ":\n")
    if different:
        for book in different: print(book)
    else: print("N/A")

def compareWithinDir(path, books):
    """
    Compares names without extensions of files within a directory (dir).
    Modify index boolean to set different similarity threshold (default: index >= 0.9).
    !!! Complexity is O(n^2) and similarity ratios are slow to compute, so expect long running time for large inputs. !!!
    Prints a list of:
        pairs of similar files (a filename can be similar to multiple filenames)
    !!! List of similar books contains double entries for pair of book1 : book2 and book2 : book1. !!!
    !!! False positives: distinct books with similar author(s) and/or title. !!!
    :param path: full path to a dir with files to be compared
    :param books: list of filenames from dir to be compared
    """
    similar = list()
    for book1 in books:
        if re.search(r"\.epub", book1.lower())\
                or re.search(r"\.mobi", book1.lower())\
                or re.search(r"\.pdf",book1.lower()): b1 = re.sub(r"\.\w+", "", book1)
        else: continue
        for book2 in books:
            if book1 != book2\
                    and (re.search(r"\.epub", book2.lower())\
                    or re.search(r"\.mobi", book2.lower())\
                    or re.search(r"\.pdf", book2.lower())):
                b2 = re.sub(r"\.\w+", "", book2)
                index = difflib.SequenceMatcher(None, b1, b2).quick_ratio()
                if index >= 0.9: similar.append((b1, b2))
    print("\nBooks in", path, "similar to books:\n")
    if similar:
        for pair in similar: print(str(pair)[1:-1])
    else: print("N/A")

def compareSize(path, books):
    """
    Compares file sizes of identical filenames (excluding extension) between two directories (dir1, dir2).
    !!! Complexity is O(log n). It is assumed and required that os.listdir returns a sorted array of filenames! !!!
    Set min difference between file sizes expressed as a share of sum of both file sizes (0 > share > 1):
        e.g. 0 returns all file pairs regardless of difference in file size
        e.g. 0.1 returns files iff size of file2 is <= 90% of size of file1
        e.g. 0.4 returns files iff size of file2 <= 60% of size of file1
        e.g. 1 returns empty list
    !!! Order of dirs is important. Function searches for files in dir1 that are larger than identical files in dir2. !!!
    !!! Run with reversed dirs to find files in dir2 that are larger than identical files in dir1. !!!
    :param path: full path to a dir with files to be compared
    :param books: list of filenames from dir to be compared
    """
    path2 = input("Enter path to other directory with books to compare: ")
    while True:
        share = input("Enter min difference to check between file sizes as a share of file size (0 > share > 1): ")
        try: share = float(share)
        except TypeError: print("\nEnter a valid share.")
        if share >= 0 and share <= 1: break
        else: print("\nEnter a valid share.")
    books2 = os.listdir(path2)
    identical = list()
    if path2[-1] != "\\": path2 = path2 + "\\"
    for book1 in books:
        if re.search(r"\.epub", book1.lower())\
                or re.search(r"\.mobi", book1.lower())\
                or re.search(r"\.pdf", book1.lower()): b1 = re.sub(r"\.\w+", "", book1).lower()
        else: continue
        lower = 0
        upper = len(books2)
        while True:
            if lower > upper: break
            book2 = books2[((lower + upper) // 2)]
            if re.search(r"\.epub", book2.lower())\
                    or re.search(r"\.mobi", book2.lower())\
                    or re.search(r"\.pdf", book2.lower()):
                b2 = re.sub(r"\.\w+", "", book2).lower()
                if b1 == b2:
                    size1 = os.path.getsize(path + book1)
                    size2 = os.path.getsize(path2 + book2)
                    if size1 > size2 and size1 - size2 >= size1 * share:
                        identical.append((size1, size2, "+" + str(round((((size1 - size2) / size1) * 100), 1)) + "%", re.sub(r"\.\w+", "", book1)))
                    break
                elif b1 < b2: upper = ((lower + upper) // 2) - 1
                else: lower = ((lower + upper) // 2) + 1
            elif b1 < b2: upper = ((lower + upper) // 2) - 1
            else: lower = ((lower + upper) // 2) + 1
    identical.sort(reverse=True)
    print("\nFILE SIZE 1  FILE SIZE 2  +%      FILE NAME\n")
    for pair in identical: print("{:>11}  {:>11}  {:>6}  {:}"
                                 .format("{:,}".format(pair[0]),
                                         "{:,}".format(pair[1]),
                                         pair[2],
                                         pair[3]))

def imageSize(path, books):
    """
    Displays filesize for cover.jp[e]g and directory size for \images above a specified threshold.
    Optional limit of maximum number of images in \images per book to check.
    !!! Works only on .epub format files. !!!
    :param path: full path to a dir with files to have images checked
    :param books: list of filenames from dir to have images checked
    """
    cover = 100000
    images = 1000000
    limit = float("inf")
    flag_cover = True
    flag_images = True
    while True:
        try:
            input_cover_str = input("Enter threshold cover.jpg filesize in bytes, D for default (100,000 bytes or 100 KB), or I to ignore checking: ")
            if input_cover_str in ["d", "D"]: break
            if input_cover_str in ["i", "I"]:
                flag_cover = False
                break
            input_cover = int(input_cover_str)
            assert input_cover >= 0
            cover = input_cover
            break
        except (ValueError, AssertionError) as e: print("Filesize must be a non-negative integer.")
    while True:
        try:
            input_images_str = input("Enter threshold \\images directory size in bytes, D for default (1,000,000 bytes or 1,000 KB), or I to ignore checking: ")
            if input_images_str in ["d", "D"]: break
            if input_images_str in ["i", "I"]:
                flag_images = False
                break
            input_images = int(input_images_str)
            assert input_images >= 0
            images = input_images
            break
        except (ValueError, AssertionError) as e: print("Directory size must be a non-negative integer.")
    if flag_images:
        while True:
            try:
                input_limit_str = input("Enter maximum number of images per book to check or D for default (no limit): ")
                if input_limit_str in ["d", "D"]: break
                input_limit = int(input_limit_str)
                assert input_limit >= 0
                limit = input_limit
                break
            except (ValueError, AssertionError) as e:
                print("Maximum number of images must be a non-negative integer.")
    if not (flag_cover or flag_images): return print("\nNo image checked.")
    print()
    for book in books:
        if re.search(r"\.epub", book.lower()):
            size_cover = 0
            size_images = 0
            counter = 0
            for info in ZF(path + book).infolist():
                if flag_cover and info.filename.lower() in ["cover.jpg", "cover.jpeg"]: size_cover = int(info.file_size)
                if flag_images and "images/" in info.filename.lower():
                    size_images += int(info.file_size)
                    counter += 1
            if flag_cover and size_cover > cover: print("File cover.jpg in book {} larger than {} bytes -> {} bytes ({}%)."
                                                        .format(book,
                                                                cover,
                                                                size_cover,
                                                                round(size_cover / cover * 100, 1)))
            if flag_images and limit >= counter and size_images > images: print("Directory \\images in book {} larger than {} bytes -> "
                                                                                "{} bytes ({}%, {} images)."
                                                                                .format(book,
                                                                                        images,
                                                                                        size_images,
                                                                                        round(size_images / images * 100, 1),
                                                                                        counter))

def imageAll(path, books):
    """
    List cover.jp[e]g files and \images directories for all books in .epub format, sorted by size descending.
    :param path: full path to a dir with files to have images checked
    :param books: list of filenames from dir to have images checked
    """
    covers = list()
    images = list()
    for book in books:
        if re.search(r"\.epub", book.lower()):
            size_images = 0
            counter = 0
            for info in ZF(path + book).infolist():
                if info.filename.lower() in ["cover.jpg", "cover.jpeg"]: covers.append((info.file_size, book))
                if "images/" in info.filename.lower():
                    size_images += int(info.file_size)
                    counter += 1
            if size_images: images.append((size_images, book, str(counter)))
    covers.sort(reverse=True)
    images.sort(reverse=True)
    print()
    for c in covers:
        if len(c[1]) > 51: print("cover.jp[e]g in {:<55} {:>7} bytes".format(c[1][:51] + "...", c[0]))
        else: print("cover.jp[e]g in {:<55} {:>7} bytes".format(c[1], c[0]))
    print()
    for i in images:
        if len(i[1]) > 54: print("\images in {:<60} {:>7} bytes {:>6} images".format(i[1][:54] + "...", i[0], i[2]))
        else: print("\images in {:<60} {:>7} bytes {:>6} images".format(i[1], i[0], i[2]))

def checkCollectionsDB(books):
    """
    Checks book filenames in collections in KoboReader.sqlite database
    and compares them against a list of actual book filenames on device.
    Run cleanCollectionsDB(books, device) for removing book filenames
    from KoboReader.sqlite database not found in actual book filenames on device.
    :param books: list of filenames from dir to be checked against database
    :param device: path to the main dir of Kobo device
    """
    device = input("Enter path to the main directory of Kobo device: ")
    if device[-1] != "\\": device = device + "\\"
    books_sorted = sorted(books)
    counter = 0
    connection = sqlite3.connect(device + ".kobo\\KoboReader.sqlite")
    cursor = connection.cursor()
    cursor.execute("SELECT ShelfName, ContentId FROM ShelfContent")
    print("\n")
    for row in cursor.fetchall():
        book = re.sub(r".+/", "", row[1])
        if not binarySearch(books_sorted, book):
            counter += 1
            print("Entry {} from collection {} not found in book filenames on device.".format(book, row[0]))
    connection.commit()
    connection.close()
    print("\nProcess finished. {} entries not found in book filenames on device.".format(str(counter)))

def cleanCollectionsDB(books):
    """
    Checks book filenames in collections in KoboReader.sqlite database
    and compares them against a list of actual book filenames on device.
    Removes entries with book filenames not found on device from KoboReader.sqlite database.
    Optional: creates backup of KoboReader.sqlite database and stores it in the same dir as KoboReader - Copy.sqlite.
    :param books: list of filenames from dir to be checked against database
    :param device: path to the main dir of Kobo device
    """
    device = input("Enter path to the main directory of Kobo device: ")
    if device[-1] != "\\": device = device + "\\"
    books_sorted = sorted(books)
    counter = 0
    while True:
        backup = input("\nCreate a backup of KoboReader.sqlite database? Y/N ")
        if backup in ["Y", "N", "y", "n"]: break
        else: print("Enter a valid choice.")
    if backup in ["Y", "y"]:
        print("\nCreating backup of KoboReader.sqlite database...")
        # creates backup of database
        copy2(device + ".kobo\\KoboReader.sqlite", device + ".kobo\\KoboReader - Copy.sqlite")
        print("Backup of KoboReader.sqlite database created in location {}.kobo\\KoboReader - Copy.sqlite".format(device))
    print("\n")
    connection = sqlite3.connect(device + ".kobo\\KoboReader.sqlite")
    cursor = connection.cursor()
    cursor.execute("SELECT ShelfName, ContentId FROM ShelfContent")
    for row in cursor.fetchall():
        book = re.sub(r".+/", "", row[1])
        if not binarySearch(books_sorted, book):
            cursor.execute("DELETE FROM ShelfContent WHERE ContentId = ?", (row[1],))
            counter += 1
            print("Entry {} from collection {} removed from database.".format(book, row[0]))
    connection.commit()
    connection.close()
    print("\nProcess finished. {} entries removed from collections.".format(str(counter)))

def binarySearch(iterable, item):
    """
    Performs a binary search on a sorted iterable.
    !!! Requires a sorted iterable. !!!
    :param iterable: iterable to search
    :param item: item to search for
    :return: if item found: item; if item not found: False
    """
    low = 0
    high = len(iterable)
    while high > low:
        mid = (low + high) // 2
        if iterable[mid] == item: return item
        elif iterable[mid] < item: low = mid + 1
        else: high = mid
    return False

### MAIN ###

undo = dict()
path = getPath()
books = getBooks(path)
while True:
    while True:
        choice = input("{} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {} {}"
                       .format("\n0: enter new path",
                               "\n1: refresh list of books from path",
                               "\n2: select individual books for processing",
                               "\n3: remove multiple spacing",
                               "\n4: fix comma spacing",
                               "\n5: fix apostrophes",
                               "\n6: find hyphen without spacing",
                               "\n7: find possible missing authors at the start",
                               "\n8: find possible missing capitalization",
                               "\n9: find books containing possible subtitles",
                               "\n10: preserve title(s) only (crop author(s), subtitle(s))",
                               "\n11: preserve author(s) and title(s) (crop subtitle(s))",
                               "\n12: restore author(s) data to filename(s) w/o author(s) data",
                               "\n13: remove substring from filename",
                               "\n14: restore filenames after modification",
                               "\n15: compare filenames from two directories",
                               "\n16: compare filenames within single directory",
                               "\n17: compare file sizes of identical books",
                               "\n18: find image files above threshold size (.epub format only)",
                               "\n19: list all cover.jp[e]g files and \\images directories sorted by size (.epub format only)",
                               "\n20: check the database on Kobo device for inaccurate collections data",
                               "\n21: remove inaccurate collections data from the database on Kobo device",
                               "\n22: choose a book at random",
                               "\n\nEnter number, H+number for help, or X for exit: "))
        if choice == "X" or choice == "x": quit()
        elif choice == "H0" or choice == "h0":   print("Changes path to directory with book filenames.")
        elif choice == "H1" or choice == "h1":   print("Refreshes list of books from path.")
        elif choice == "H2" or choice == "h2":   help(selectBooks)
        elif choice == "H3" or choice == "h3":   help(removeMultipleSpacing)
        elif choice == "H4" or choice == "h4":   help(fixCommaSpacing)
        elif choice == "H5" or choice == "h5":   help(fixApostrophes)
        elif choice == "H6" or choice == "h6":   help(findHypenWithoutSpacing)
        elif choice == "H7" or choice == "h7":   help(findNoAuthorFirst)
        elif choice == "H8" or choice == "h8":   help(findMissingCapitalization)
        elif choice == "H9" or choice == "h9":   help(findSubtitles)
        elif choice == "H10" or choice == "h10": help(withoutAuthors)
        elif choice == "H11" or choice == "h11": help(withAuthors)
        elif choice == "H12" or choice == "h12": help(restoreAuthors)
        elif choice == "H13" or choice == "h13": help(removeSubstring)
        elif choice == "H14" or choice == "h14": help(restoreOld)
        elif choice == "H15" or choice == "h15": help(compareTwoDirs)
        elif choice == "H16" or choice == "h16": help(compareWithinDir)
        elif choice == "H17" or choice == "h17": help(compareSize)
        elif choice == "H18" or choice == "h18": help(imageSize)
        elif choice == "H19" or choice == "h19": help(imageAll)
        elif choice == "H20" or choice == "h20": help(checkCollectionsDB)
        elif choice == "H21" or choice == "h21": help(cleanCollectionsDB)
        elif choice == "H22" or choice == "h22": help(random)
        else:
            try:
                number = int(choice)
                start = time()
                if number == 0:
                    print()
                    undo = dict()
                    path = getPath()
                    books = getBooks(path)
                    print("New path:", path)
                    break
                if number == 1:
                    print()
                    books = getBooks(path)
                    print("List of books from path {} refreshed.".format(path))
                    break
                if number == 2:
                    print()
                    books = selectBooks()
                    break
                elif number == 3:
                    print()
                    removeMultipleSpacing(path, books, undo)
                    break
                elif number == 4:
                    print()
                    fixCommaSpacing(path, books, undo)
                    break
                elif number == 5:
                    print()
                    fixApostrophes(path, books, undo)
                    break
                elif number == 6:
                    print()
                    findHypenWithoutSpacing(path, books)
                    break
                elif number == 7:
                    print()
                    findNoAuthorFirst(path, books)
                    break
                elif number == 8:
                    print()
                    findMissingCapitalization(path, books)
                    break
                elif number == 9:
                    print()
                    findSubtitles(books)
                    break
                elif number == 10:
                    print()
                    withoutAuthors(path, books, undo)
                    break
                elif number == 11:
                    print()
                    withAuthors(path, books, undo)
                    break
                elif number == 12:
                    print()
                    restoreAuthors(path, books, undo)
                    break
                elif number == 13:
                    print()
                    removeSubstring(path, books, undo)
                    break
                elif number == 14:
                    print()
                    restoreOld(path, undo)
                    break
                elif number == 15:
                    print()
                    compareTwoDirs(path, books)
                    break
                elif number == 16:
                    print()
                    compareWithinDir(path, books)
                    break
                elif number == 17:
                    print()
                    compareSize(path, books)
                    break
                elif number == 18:
                    print()
                    imageSize(path, books)
                    break
                elif number == 19:
                    print()
                    imageAll(path, books)
                    break
                elif number == 20:
                    print()
                    checkCollectionsDB(books)
                    break
                elif number == 21:
                    print()
                    cleanCollectionsDB(books)
                    break
                elif number == 22:
                    print()
                    print(ch(books))
                    break
                else: print("\nEnter a valid number.")
            except ValueError: print("\nEnter a valid choice.")
print("\nFinished in %s seconds." % "{0:.3f}".format(time() - start))