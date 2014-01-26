#imports
import urllib2
from urllib2 import HTTPError
import re
import sys

#constants
sjsu_home_url = "http://www.sjsu.edu"
faculty_list_url = "http://www.sjsu.edu/people/a-z.jsp"
courses_pattern = re.compile('\/people\/.*\/courses\/')
course_pattern = re.compile('\/courses\/(.*)"')
publications_pattern = re.compile('\/publications\/')
research_pattern = re.compile('\/research\/')
expert_pattern = re.compile('\/expert\/')
course_content_pattern = re.compile(
    '<div id="col_1_of_1_int_maintemplate">(.*)<div id="disclaimer_people">',re.S)
faculty_link_pattern = re.compile(
    '<li><a href="(/people/.*)">.*</a></li>')
page_contents_pattern = re.compile(
    '<div id="pagetitle">(.*)<div id="disclaimer_people">', re.S)

# Functions

# Process one faculty site
def  process_faculty_home_page(faculty_home_url):
    # print "processing "+faculty_home_url
    try:
        faculty_page = urllib2.urlopen(faculty_home_url)
    except HTTPError, e:
        print e.code
        sys.exit()
    # print data.read()
    faculty_page_raw = faculty_page.read()
    publications_link = re.findall(publications_pattern, faculty_page_raw)
    courses_links = re.findall(courses_pattern, faculty_page_raw)
    research_link = re.findall(research_pattern, faculty_page_raw)
    expert_link = re.findall(expert_pattern, faculty_page_raw)
        
    has_publications_page = False
    has_all_courses_page = False
    has_expert_page = False
    has_research_page = False
        
    if (len(publications_link) > 0):
        has_publications_page = True
        publications_url = faculty_home_url + '/publications/'
                
    if (len(courses_links) > 0):
        has_all_courses_page = True
        courses_url = faculty_home_url + '/courses/'
                
    if (len(expert_link) > 0):
        has_expert_page = True
        expert_url = faculty_home_url + '/expert/'
                
    if (len(research_link) > 0):
        has_research_page = True
        research_url = faculty_home_url + '/research/'
                
    # Get faculty info
    faculty_page_match = page_contents_pattern.search(faculty_page_raw)
    if faculty_page_match:
        faculty_page_contents = faculty_page_match.group(1)
    
    # Get expert info
    if has_expert_page:
        print "Found expert at " + expert_url
        expert_contents = get_page_contents(expert_url, 
                                            page_contents_pattern)
        # print expert_contents
        
    # Get research info
    if has_research_page:
        print "Found research at " + research_url
        research_contents = get_page_contents(research_url, 
                                              page_contents_pattern)
        # print research_contents
    
    # Get publications info    
    if has_publications_page:
        print "Found publications at " + publications_url
        publications_contents = get_page_contents(publications_url, 
                                                  page_contents_pattern)
        # print publications_contents
        
    #  Get  course  info
    if has_all_courses_page:
        print  "Found courses at " + courses_url
        try:
            all_courses_page = urllib2.urlopen(courses_url)
            all_courses_raw = all_courses_page.read()
            all_course_links = re.findall(
                                          course_pattern, 
                                          all_courses_raw)
            process_faculty_courses_page(
                                         faculty_home_url, 
                                         all_course_links)
        except:
            print "Could not open page"
        
# Open a URL, read the contents, return part that matches pattern
def get_page_contents(page_url, content_pattern):
    try:
        page = urllib2.urlopen(page_url)
        raw = page.read()
        match = content_pattern.search(raw)
        if match:
            contents = match.group(1)
            return contents
        else:
            print "no match found in " + page_url
    except:
        print "Could not open page " + page_url

# Process all of the courses for one faculty
def process_faculty_courses_page(base_url, link_list):
    for course_link in link_list:
        course_url = base_url + "/courses/" + course_link + "/index.html"
        print "Opening course: " + course_link
        if (not(course_link.startswith('index.html')) 
                and (len(course_link)  >  0)):
            print  "Found course: " + course_url
            course_contents = get_page_contents(
                                                course_url, 
                                                course_content_pattern)
            # print course_contents
        else:
            print "Skipping link: " + course_link
            
# Main loop
if len(sys.argv) > 1:
    # print sys.argv[1]
    process_faculty_home_page(sys.argv[1])
else:
    # Get list of all published faculty sites
    data = urllib2.urlopen(faculty_list_url)
    all_faculty_links = re.findall(faculty_link_pattern, data.read())

    #  Process  each  faculty  site
    for faculty_home_link in all_faculty_links:
        current_url = sjsu_home_url + faculty_home_link
        process_faculty_home_page(current_url)
