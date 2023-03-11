import argparse

def get_static_page(url):
    """Get a static page from the web"""
    import requests
    # Get the page
    response = requests.get(url)
    # Check if the page was downloaded successfully
    if response.status_code == 200:
        return response.text
    else:
        print("Error downloading page")
        return None

def get_classes_from_page(page_source):
    """Get the list of classes from the page source"""
    import lxml.html as lhtml
    #convert the source to lxml, so we can use xpath
    tree = lhtml.fromstring(page_source)
    #get the list of element classes from the page
    classes = tree.xpath('//@class')
    #remove duplicates
    #check for empty classes, and remove them
    non_empty_classes = []
    for class_ in classes:
        if class_ != None:
            non_empty_classes.append(class_)
    classes = non_empty_classes
    classes = list(set(classes))
    return classes

def get_xpath_attribute_from_page_by_class(page_source, element_class, attribute):
    """Get the list of classes from the page source"""
    import lxml.html as lhtml
    try:
        #convert the source to lxml, so we can use xpath
        tree = lhtml.fromstring(page_source)
        #get the list of element classes from the page
        xpath = '//*[@class="' + element_class + '"]['+attribute+']'
        elements = tree.xpath(xpath)
        non_empty_elements = []
        for elem in elements:
            if elem != None:
                non_empty_elements.append(elem)
        return non_empty_elements
    except:
        print("Error getting elements "+str(element_class)+str(attribute))
        return None

def algorithm_A(url=None):
    """Algorithm A"""    
    if url == None:
        url = input("Enter the URL of the page you want to scrape: ") #get url
    static_source = get_static_page(url)#get the static page
    unique_element_classes = get_classes_from_page(static_source)#get the unique element classes
    print("Unique element classes: " + str(len(unique_element_classes)))

    #a structure where one of the valeus is the name of the unique class, the other is an array of the found elements
    class_elements = []
    for class_ in unique_element_classes:#for each unique class, get the text,href,and title attributes, or custom ones
        href_elements = get_xpath_attribute_from_page_by_class(static_source, class_, "@href")#elements of that class that have href attributes
        text_elements = get_xpath_attribute_from_page_by_class(static_source, class_, "text()")#elements of that class that have text attributes
        title_elements = get_xpath_attribute_from_page_by_class(static_source, class_, "@title")#elements of that class that have title attributes
        class_elements.append([class_, href_elements, text_elements, title_elements])
    return class_elements

def algorithm_B(arr_custom_attributes, url=None):
    """Algorithm B - takes an array of custom attributes, that will be scanned for each element class \n input_type:[str,str,str,str...] \nreturn type:[class_, href_elements, text_elements, title_elements, custom_elements]"""
    if url == None:
        url = input("Enter the URL of the page you want to scrape: ") #get url
    static_source = get_static_page(url)#get the static page
    unique_element_classes = get_classes_from_page(static_source)#get the unique element classes
    print("Unique element classes: " + str(len(unique_element_classes)))

    #a structure where one of the valeus is the name of the unique class, the other is an array of the found elements
    class_elements = []
    for class_ in unique_element_classes:#for each unique class, get the text,href,and title attributes, or custom ones
        custom_elements = []
        for custom_attribute in arr_custom_attributes:
            custom_elements.append(get_xpath_attribute_from_page_by_class(static_source, class_, custom_attribute))
        class_elements.append([class_, custom_elements])
    return class_elements

def algorithm_C():
    """Algorithm C - opens a headless browser, lets the user log in, and then scouts the page. While the browser is still open, will do the page scouting and allow the user to select the classes, and then, would proceed to dynamically mine the contents of the page, after getting user confirmation"""
    import selenium
    from selenium import webdriver
    import flask

    #open the headless browser and let the user navigate and log in, ask for confirmation in the terminal
    browser = webdriver.Chrome()
    browser.get("https://google.com")
    input("Press enter when you are done navigating and logging in: ")
    input("Press enter to continue: ")
    #get the page source
    page_source = browser.page_source
    #get the unique classes
    unique_element_classes = get_classes_from_page(page_source)
    #display the classes in a table
    temp_table = []
    for class_ in unique_element_classes:
        href = get_xpath_attribute_from_page_by_class(page_source, class_, "@href")
        text = get_xpath_attribute_from_page_by_class(page_source, class_, "text()")
        title = get_xpath_attribute_from_page_by_class(page_source, class_, "@title")
        temp_table.append([class_, href, text, title])
    #display the table
    table = []
    for class_ in temp_table:
        for i in range(1, len(class_)):
            for element in class_[i]:
                if i == 1:
                    table.append([class_[0], "href", len(element), str(element.text_content())+"\n"])
                elif i == 2:
                    table.append([class_[0], "text", len(element), str(element.text_content())+"\n"])
                elif i == 3:
                    table.append([class_[0], "title", len(element), str(element.text_content())+"\n"])
                else:
                    table.append([class_[0], "custom", len(element), str(element.text_content())+"\n"])
    flask_display_engine(table=table)

    #get the class to use
    class_to_use = input("Enter the class you want to use: ")
    attribute_of_class = input("Enter the attribute of the class you want to use: ")

    while True:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        page_source = browser.page_source
        elements = get_xpath_attribute_from_page_by_class(page_source, class_to_use, attribute_of_class)
        print(elements)
        if input("Enter q to quit, or enter to continue: ") == "q":
            break
    
def flask_display_engine(table):
    """Display the table using flask"""
    import flask
    app = flask.Flask(__name__)
    @app.route("/")
    def index():
        return flask.render_template("index.html", table=table)
    
    @app.route("/save", methods=["POST"])
    def save():
        import csv
        with open("output.csv", "w",encoding="ascii") as f:
            writer = csv.writer(f)
            writer.writerows(table)
        return "Saved"
    app.run()
    #wait for user to input the class index to use
    class_index = input("Enter the index of the class you want to use: ")
    return table[int(class_index)]


def main():
    import flask
    """Main Function"""
    #gets the arguments from the command line : -a (algorithm) -c (custom attributes)
    parser = argparse.ArgumentParser()
    parser.add_argument("-sa", help="Scout algorithm - 'A' or 'B' \n A - would scan for href,text,title attributes \n B - would scan for custom attributes\nC - would open a headless browser, let the user log in, and then scout the page. While the browser is still open, will do the page scouting and allow the user to select the classes, and then, would proceed to dynamically mine the contents of the page, after getting user confirmation ")
    parser.add_argument("-u", help="URL of the page to scrape")
    parser.add_argument("-c", help="Custom attributes to use")
    parser.add_argument("-o", help="Output file")
    parser.add_argument("-rt", help="Refresh time - 0 - would make the page scroll indefinetely")
    parser.add_argument("-s", help="Scrolling speed")
    
    #parser.add_argument("-oF", help="Output format")
    args = parser.parse_args()
    url = args.u
    output_file = args.o
    mined_classes = []
    if args.sa == "A":
        mined_classes = algorithm_A()
    elif args.sa == "B":
        mined_classes = algorithm_B(args.c.split(","))
    elif args.sa == "C":
        algorithm_C()
        exit()
    else:
        print("Invalid algorithm")
        exit()
    
    table = []
    for class_ in mined_classes:
        for i in range(1, len(class_)):
            for element in class_[i]:
                if i == 1:
                    table.append([class_[0], "href", len(element), str(element.text_content())+"\n"])
                elif i == 2:
                    table.append([class_[0], "text", len(element), str(element.text_content())+"\n"])
                elif i == 3:
                    table.append([class_[0], "title", len(element), str(element.text_content())+"\n"])
                else:
                    table.append([class_[0], "custom", len(element), str(element.text_content())+"\n"])

    flask_display_engine(table)

if __name__ == "__main__":
    main()

    
