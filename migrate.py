''' 
TODO:

download and save binaries

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

course_name_pattern = re.compile('\/courses\/(.*)"')

faculty_directory_pattern = re.compile('http://www.sjsu.edu/people/(.*)/?')

course_content_pattern = re.compile(
    '<div id="col_1_of_1_int_maintemplate">(.*)<div id="disclaimer_people">',re.S)

faculty_link_pattern = re.compile('<li><a href="(/people/.*)">.*</a></li>')    

page_contents_pattern = re.compile(
    '<div id="pagetitle">.*?</div>(.*)</div>.*?</div>.*?<div id="disclaimer_people">', re.S)

page_contents_pattern_b = re.compile(
    '<div id="pagetitle">.*?</div>(.*)<div id="disclaimer_people">', re.S)
    
page_contents_pattern_c = re.compile(
    '<!-- start column one -->(.*)<!-- end column one -->', re.S)

page_title_pattern = re.compile('<div id="pagetitle">.*?<h2>(.*)</h2>', re.S)

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
    
# Replace unknown entities and unclosed BR tags
def cleanup_code(code_in):
    if code_in:
        code_out = code_in.replace('&nbsp;', ' ').replace('<br>', '<br />')
        code_out = unescaped_ampersand_pattern.sub('&amp;', code_out)
        return code_out
    else:
        return ""
    
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
        return error_message

# Read a generic page and output its content
def output_page(faculty_name, page_url, page_name):
    faculty_root = output_root + faculty_name
    site_section = last_element_pattern.match(page_url).group(1)
    if (site_section == '/publications/' 
        or site_section == '/research/'
        or site_section == '/expert/'):
        # print "Publications or Research page"
        page_contents = get_page_contents(page_url)
        if (page_contents == ""):
            print "No match found in " + page_url
            
    elif (site_section == '/courses/'):
        process_faculty_courses_page(page_url)
        return
    else:
        page_contents = get_page_contents(page_url)
    
    if (not page_contents or page_contents == ""):
        print "empty page " + page_url
    else:
        page_contents = cleanup_code(page_contents)
        # Get full name
        full_name = get_page_title(page_url)
        if not full_name:
            print "Page title not found " + page_url
        
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
        if not link_text == "Home":
            output_page(fix_name(faculty_name), sjsu_home_url + link_url, link_text)
            sidenav_content += '<li><a href="' + fix_name(link_url) + '">' + link_text + '</a></li>'
    
    sidenav_output = open(output_directory + '/sidenav.inc', 'w+')
    sidenav_output.write(sidenav_content)
    sidenav_output.close()
    
    # Read Faculty Home Page
    # faculty_page_match = page_contents_pattern.search(faculty_page_raw)
 
    # Get full name
    full_name = get_page_title(faculty_home_url)

    faculty_page_match = page_contents_pattern_b.search(faculty_page_raw)
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
       
# Open a course, read the contents, return part that matches pattern
def get_course_page_contents(page_url):
    try:
        page = urllib2.urlopen(page_url)
        raw = page.read()
        match = course_content_pattern.search(raw)
        if match:
            contents = match.group(1)
            return contents
        else:
            print "No course content found in " + page_url
            print raw
            return ""
    except:
        print "Could not open page " + page_url
      
          # get contents of courses page
def get_courses_page_contents(page_url):
    print "opening " + page_url
    try:
        page = urllib2.urlopen(page_url)
        raw = page.read()
        match = courses_page_contents_pattern.search(raw)
        if match:
            contents = match.group(1)
            return contents
        else:
            print "No course content found in " + page_url
            print raw
            return ""
    except Exception as e:
        error_message = str(e.args)
        print error_message + " at " + page_url
    
def get_page_title(page_url):
    try:
        page = urllib2.urlopen(page_url)
        raw = page.read()
        match = page_title_pattern.search(raw)
        if match:
            contents = match.group(1)
            return contents
            
    except Exception as e:
        error_message = str(e.args)
        print error_message + " at " + page_url       
                
# Open a URL, read the contents, return part that matches pattern
def get_page_contents(page_url):
    try:
        page = urllib2.urlopen(page_url)
        raw = page.read()
        match = courses_page_contents_pattern.search(raw)
        if match:
            contents = match.group(1)
            return contents
        else:
            match = page_contents_pattern_b.search(raw)
            if match:
                contents = match.group(1)
                return contents
            else:
                match = page_contents_pattern_c.search(raw)
                if match:
                    contents = match.group(1)
                    return contents
                else:
                    match = course_contents_pattern.search(raw)
                    if match:
                        contents = match.group(1)
                        return contents
                    else:
                        print "No match found in " + page_url
                        return ""
    except Exception as e:
        error_message = str(e.args)
        print error_message + " at " + page_url

# Process all of the courses for one faculty
def process_faculty_courses_page(courses_url):
    name_pattern = re.compile('http://www.sjsu.edu/people/(.*)/courses')
    faculty_name = name_pattern.match(courses_url).group(1)
    print "Getting courses for " + faculty_name
    # Get list of courses
    print "getting content from " + courses_url
    courses_page_contents = get_courses_page_contents(courses_url)
                                            
    # print course_page_contents
    link_list = re.findall(course_name_pattern, 
                                          courses_page_contents)
    sidenav = ""
    output_dir = output_root + fix_name(faculty_name)
    # Process all course links
    for course_name in link_list:
        course_url = courses_url + course_name
        print "Reading: " + course_name
        
        # Make sure this is a valid link
        if (not(course_name.startswith('index.html')) 
                and (len(course_name)  >  0)):
            # print "Reading course: " + course_url
            sidenav_link = '/' + output_dir + '/courses/' + course_name + '/'
            sidenav += '<li><a href="' + sidenav_link + '">' + course_name + '</a></li>\n'
            
            course_contents = get_course_page_contents(course_url)
            if (course_contents):
                # print course_contents
                course_directory = output_dir + '/courses/' + course_name
                # print "New course directory: " + course_directory
                if not os.path.exists(output_dir + '/courses/' + course_name):
                    os.makedirs(output_dir + '/courses/' + course_name)
                course_output = open(output_dir + '/courses/' + course_name +'/index.pcf', 'w+')
                course_output.write(course_contents)
                course_output.close()
                sidenav_output = open(output_dir + '/courses/sidenav.inc', 'w+')
                sidenav_output.write(sidenav)
                sidenav_output.close()
            else:
                print "No content found in " + course_name
          
    
    
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
