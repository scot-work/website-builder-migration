#imports
import urllib2
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
course_content_pattern = re.compile('<div id="col_1_of_1_int_maintemplate">(.*)<div id="disclaimer_people">',re.S)
faculty_link_pattern = re.compile('<li><a href="(/people/.*)">.*</a></li>')
home_page_contents_pattern = re.compile('<div id="pagetitle">(.*)<div id="disclaimer_people">', re.S)

# Functions
def  process_faculty(faculty_home_url):
    # print "processing "+faculty_home_url
    faculty_page = urllib2.urlopen(faculty_home_url)
    # print data.read()
    faculty_page_raw = faculty_page.read()
    publications_link = re.findall(publications_pattern, 
                                   faculty_page_raw)
    courses_links = re.findall(courses_pattern, faculty_page_raw)
    research_link = re.findall(research_pattern, faculty_page_raw)
    expert_link = re.findall(expert_pattern, faculty_page_raw)
    faculty_page_contents = home_page_contents_pattern.search(faculty_page_raw)
        
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
                
    if (has_publications_page):
        publications_source = urllib2.urlopen(publications_url)
                
    #  Get  course  data
    if (has_all_courses_page):
        print  "Found courses at " + courses_url
        try:
            all_courses_page = urllib2.urlopen(courses_url)
        except:
            print "Could not open page " + courses_url
        all_courses_raw = all_courses_page.read()
        all_course_links = re.findall(course_pattern, all_courses_raw)
        process_courses(faculty_home_url, all_course_links)

def process_courses(base_url, link_list):
    for course_link in link_list:
        course_url = base_url + "/courses/" + course_link + "/index.html"
        print "Opening course: " + course_link
        if (not(course_link.startswith('index.html')) and (len(course_link)  >  0)):
            print  "Found course: " + course_url
            course_page = urllib2.urlopen(course_url)
            course_raw = course_page.read()
            course_match = course_content_pattern.search(course_raw)
            if course_match:
                course_content = course_match.group(1)
                print course_content
            else:
                print "no match found"
        else:
            print "Skipping link: " + course_link
#  Get list of all active faculty sites
data = urllib2.urlopen(faculty_list_url)

all_faculty_links = re.findall(faculty_link_pattern, data.read())
print "Found " + str(len(all_faculty_links)) + " faculty sites"

#  Process  each  faculty  site
for faculty_home_link in all_faculty_links:
    current_url = sjsu_home_url + faculty_home_link
    process_faculty(current_url)

print "done processing"
