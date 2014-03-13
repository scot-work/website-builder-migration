''' 
TODO:

Validate XML http://lxml.de/validation.html
courses page content pattern
Need to fix unclosed <p> tags
sidenav.inc in every directory

'''
#imports
import urllib2
from urllib2 import HTTPError
import re
import sys
import os
from lxml import etree
from lxml.etree import XMLParser
import StringIO

#constants
sjsu_home_url = "http://www.sjsu.edu"
output_root = "people/"
errors_root = "errors/"
faculty_list_url = "http://www.sjsu.edu/people/a-z.jsp"
# courses_pattern = re.compile('\/people\/.*\/courses\/')
faculty_directory_pattern = re.compile('http://www.sjsu.edu/people/(.*)/?')

course_content_pattern = re.compile(
    '<div id="col_1_of_1_int_maintemplate">(.*)<div id="disclaimer_people">',re.S)

faculty_link_pattern = re.compile('<li><a href="(/people/.*)">.*</a></li>')    

page_contents_pattern = re.compile(
    '<div id="pagetitle">.*?</div>(.*)</div>.*?</div>.*?<div id="disclaimer_people">', re.S)

publications_contents_pattern = re.compile(
    '<div id="pagetitle">.*?</div>(.*)<div id="disclaimer_people">', re.S)

full_name_pattern = re.compile('<div id="pagetitle">.*?<h2>(.*)</h2>', re.S)

unescaped_ampersand_pattern = re.compile('&(?!amp;)')

courses_page_contents_pattern = re.compile('<h3>Courses</h3>.*?<ul>(.*)</ul>', re.S)
# courses_page_contents_pattern = re.compile('<div id="pagetitle">.*?</div>(.*)</div>.*?</div>.*?<div id="disclaimer_people">', re.S)

primary_navigation_pattern = re.compile(
    '<div class="primary_top">(.*)<!-- end primary navigation -->', re.S)
    
link_pattern = re.compile('<a href="(.*)">(.*)</a>')

last_element_pattern = re.compile('.*(/.*/)')

faculty_name_pattern = re.compile('http://www.sjsu.edu/people/(.*)')

page_title_placeholder_pattern = re.compile('{{.*?}}')

standard_navigation_links = ["Courses", 
                             "Publications &amp; Presentations", 
                             "Research &amp; Scholarly Activity", 
                             "University Expert", 
                             "Professional &amp; Service Activity"]
# Functions

# Periods and apostrophes are not allowed in OU, so replace in directory names
def fix_name(faculty_name):
    return faculty_name.replace('.', '-').replace("'", "")
    
def cleanup_code(code_in):
    # Replace unknown entities and unclosed tags
    code_out = code_in.replace('&nbsp;', ' ').replace('<br>', '<br />')
    code_out = unescaped_ampersand_pattern.sub('&amp;', code_out)
    return code_out
    
# Determine if this is valid XML
def validate(content):
    valid = True
    parser = etree.XMLParser(dtd_validation=True)
    try:
        
        root = etree.fromstring(content.getvalue())
    except Exception as e:
        error_message = str(e.args)
        valid = False
    if valid:
        return "valid"
    else:
        print error_message
        return error_message

# Read a page and output its content
def output_page(faculty_name, page_url, page_name):
    faculty_root = output_root + faculty_name
    # print "Writing directory: " + faculty_root + " url: " + page_url + " name " + page_name
    site_section = last_element_pattern.match(page_url).group(1)
    if (site_section == '/publications/' 
        or site_section == '/research/'
        or site_section == '/expert/'):
        # print "Publications or Research page"
        page_contents = get_page_contents(page_url, publications_contents_pattern)
    elif (site_section == '/courses/'):
        process_faculty_courses_page(page_url)
        return
    else:
        page_contents = get_page_contents(page_url, page_contents_pattern)
    
    page_contents = cleanup_code(page_contents)

    # Get full name
    full_name = get_page_contents(page_url, full_name_pattern)
    # print "Faculty Name is " + full_name
    
    # Get directory name from URL and create directory
    directory_name = last_element_pattern.match(page_url).group(1)
    if not os.path.exists(faculty_root + '/' + directory_name + '/'):
        os.makedirs(faculty_root + '/' + directory_name + '/')
    
    # Read beginning and end of pcf file
    with open ("header.txt", "r") as myfile:
        page_header = myfile.read()
        page_header = page_header.replace('{{Page Title}}', full_name)
    myfile.close()
    with open ("footer.txt", "r") as myfile:
        page_footer = myfile.read()
    myfile.close()
    
    # assemble the file
    output_content = StringIO.StringIO()
    output_content.write(page_header)
    output_content.write(page_contents)
    output_content.write(page_footer)

    # Make sure content is valid
    validation_results = validate(output_content)
    if (validation_results == "valid"):
        # Open output file
        page_output = open(output_root + faculty_name + '/' + directory_name + '/index.pcf', 'w+')
        page_output.write(output_content.getvalue())
        page_output.close()
        sidenav_output = open(output_root + faculty_name + '/' + directory_name + '/sidenav.inc', 'w+')
        sidenav_output.close()
    else:
        # File is not valid XML
        error_directory = errors_root + faculty_name + '/' + directory_name + '/'
        if not os.path.exists(error_directory):
            os.makedirs(error_directory)
        error_output = open(error_directory + 'errors.xml', 'w+')
        error_output.write(validation_results + output_content.getvalue())
        error_output.close()
    
    output_content.close()


# Process one faculty site
def  process_faculty_home_page(faculty_home_url):
    # print "processing " + faculty_home_url
    faculty_name = faculty_name_pattern.match(faculty_home_url).group(1)
    directory_name_match = faculty_directory_pattern.match(faculty_home_url)
    output_directory = output_root + fix_name(directory_name_match.group(1))
    
    try:
        faculty_page = urllib2.urlopen(faculty_home_url)
    except HTTPError, e:
        print "HTTP error opening " + faculty_home_url
        sys.exit()
    
    # Create output directory
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    home_output = open(output_directory+'/index.pcf', 'w+')
    faculty_page_raw = faculty_page.read()

    # Get links
    primary_nav_match = primary_navigation_pattern.search(faculty_page_raw)
    
    # Process Links
    links = re.findall(link_pattern, primary_nav_match.group(1))
    sidenav_content = ""
    for link in links:
        link_url = link[0]
        link_text = link[1]
        if link_text in standard_navigation_links:
            output_page(fix_name(faculty_name), sjsu_home_url + link_url, link_text)
            sidenav_content += '<li><a href="' + fix_name(link_url) + '">' + link_text + '</a></li>'
        elif not (link_text == "Home"):
            print "Processing custom page: " + link_url
            output_page(fix_name(faculty_name), sjsu_home_url + link_url, link_text)
            sidenav_content += '<li><a href="' + fix_name(link_url) + '">' + link_text + '</a></li>'
    
    sidenav_output = open(output_directory + '/sidenav.inc', 'w+')
    sidenav_output.write(sidenav_content)
    sidenav_output.close()
    
    # Read Faculty Home Page
    # faculty_page_match = page_contents_pattern.search(faculty_page_raw)
 
    # Get full name
    full_name = get_page_contents(faculty_home_url, full_name_pattern)

    faculty_page_match = publications_contents_pattern.search(faculty_page_raw)
    if faculty_page_match:
        faculty_page_contents = faculty_page_match.group(1)
        with open ("header.txt", "r") as myfile:
            page_header = myfile.read()
            page_header = page_header.replace('{{Page Title}}', full_name)
        home_output.write(page_header)
        myfile.close()
        home_output.write(faculty_page_contents)
        with open ("footer.txt", "r") as myfile:
            page_footer = myfile.read()
        home_output.write(page_footer)
        myfile.close()
        home_output.close()
    else:
        print "No regex match found on home page for " + faculty_home_url

'''def process_courses(courses_url)
    if has_all_courses_page:
        print "Found courses at " + courses_url
        try:
            courses_page = urllib2.urlopen(courses_url)
            courses_raw = courses_page.read()
            courses_page_contents = get_page_contents(courses_url, 
                                        courses_page_contents_pattern)
            if not os.path.exists(directory+'/courses/'):
                os.makedirs(directory+'/courses/')
            courses_output = open(directory+'/courses/index.pcf', 'w+')
            courses_output.write(courses_page_contents)
            courses_output.close()
            all_course_names = re.findall(course_name_pattern, courses_raw)
            process_faculty_courses_page(faculty_home_url, 
                                         all_course_names,
                                         directory)
        except Exception as e:
            print "Unexpected error: " + str(e)
'''
       
# Open a URL, read the contents, return part that matches pattern
def get_page_contents(page_url, content_pattern):
    # print "Getting contents from " + page_url
    try:
        page = urllib2.urlopen(page_url)
        raw = page.read()
        match = content_pattern.search(raw)
        if match:
            contents = match.group(1)
            return contents
        else:
            print "no match found in " + page_url
            return ""
    except:
        print "Could not open page " + page_url

# Process all of the courses for one faculty
def process_faculty_courses_page(base_url):

    sidenav = ""
    for course_name in link_list:
        course_url = base_url + "/courses/" + course_name + "/index.html"
        # print "Checking: " + course_name
        if (not(course_name.startswith('index.html')) 
                and (len(course_name)  >  0)):
            # print "Reading course: " + course_url
            sidenav_link = '/' + output_dir + '/courses/' + course_name + '/'
            sidenav += '<li><a href="'+sidenav_link+'">'+course_name+'</a></li>\n'
            
            course_contents = get_page_contents(course_url, course_content_pattern)
            if (len(course_contents) > 0):
                # print course_contents
                # print "Creating directory"
                course_directory = output_directory + '/courses/' + course_name
                # print "New course directory: " + course_directory
                if not os.path.exists(output_dir + '/courses/' + course_name):
                    os.makedirs(output_dir + '/courses/' + course_name)
                course_output = open(output_dir + '/courses/' + course_name +'/index.pcf', 'w+')
                course_output.write(course_contents)
                course_output.close()
            
    sidenav_output = open(output_directory + '/courses/sidenav.inc', 'w+')
    sidenav_output.write(sidenav)
    sidenav_output.close()
    
# Main loop
# Read command line
if not(len(sys.argv) > 1):
    print "Usage: "
    print "python migrate.py name : Process one faculty"
    print "python migrate.py all : Process all faculty"
else:
    cla = sys.argv[1]
    if not cla == "all":
        faculty_url = "http://www.sjsu.edu/people/" + cla
        process_faculty_home_page(faculty_url)
    else:
        # Get list of all published faculty sites
        data = urllib2.urlopen(faculty_list_url)
        all_faculty_links = re.findall(faculty_link_pattern, data.read())

        #  Process  each  faculty  site
        for faculty_home_link in all_faculty_links:
            current_url = sjsu_home_url + faculty_home_link
            process_faculty_home_page(current_url)
