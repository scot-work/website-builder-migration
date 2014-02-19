#imports
import urllib2
from urllib2 import HTTPError
import re
import sys
import os

#constants
sjsu_home_url = "http://www.sjsu.edu"
output_root = "people"
faculty_list_url = "http://www.sjsu.edu/people/a-z.jsp"
courses_pattern = re.compile('\/people\/.*\/courses\/')
faculty_directory_pattern = re.compile('http://www.sjsu.edu/people/(.*)/?')
course_name_pattern = re.compile('\/courses\/(.*)"')
publications_pattern = re.compile('\/publications\/')
research_pattern = re.compile('\/research\/')
expert_pattern = re.compile('\/expert\/')
course_content_pattern = re.compile(
    '<div id="col_1_of_1_int_maintemplate">(.*)<div id="disclaimer_people">',re.S)
faculty_link_pattern = re.compile(
    '<li><a href="(/people/.*)">.*</a></li>')
page_contents_pattern = re.compile(
    '<div id="pagetitle">(.*)<div id="disclaimer_people">', re.S)
courses_page_contents_pattern = re.compile(
          '<h1 class="hidden">Main Content</h1>(.*)<h1 class="hidden">', re.S)

# Functions

# Periods are not allowed in OU, so replace in directory names
def fix_dir_name(dir_name):
	return dir_name.replace('.', '-')

# Process one faculty site
def  process_faculty_home_page(faculty_home_url):
    print "processing "+faculty_home_url
    directory_name_match = faculty_directory_pattern.match(faculty_home_url)
    directory = output_root + "/" + fix_dir_name(directory_name_match.group(1))
    
    try:
        faculty_page = urllib2.urlopen(faculty_home_url)
    except HTTPError, e:
        print "HTTP error: " + e.code + " opening " + faculty_home_url
        sys.exit()
    
    # Create output directory
    if not os.path.exists(directory):
        os.makedirs(directory)
    home_output = open(directory+'/index.pcf', 'w+')
    
    faculty_page_raw = faculty_page.read()
    publications_link = re.findall(publications_pattern, faculty_page_raw)
    courses_links = re.findall(courses_pattern, faculty_page_raw)
    research_link = re.findall(research_pattern, faculty_page_raw)
    expert_link = re.findall(expert_pattern, faculty_page_raw)
        
    has_publications_page = False
    has_all_courses_page = False
    has_expert_page = False
    has_research_page = False
    
    sidenav = ""
        
    if (len(publications_link) > 0):
        has_publications_page = True
        publications_url = faculty_home_url + '/publications/'
        sidenav += '<li><a href="/'+directory+'/publications/">Publications</a></li>\n'
                
    if (len(courses_links) > 0):
        has_all_courses_page = True
        courses_url = faculty_home_url + '/courses/'
        sidenav += '<li><a href="/'+directory+'/courses/">Courses</a></li>\n'
                
    if (len(expert_link) > 0):
        has_expert_page = True
        expert_url = faculty_home_url + '/expert/'
        sidenav += '<li><a href="/'+directory+'/expert/">Expert</a></li>\n'
                
    if (len(research_link) > 0):
        has_research_page = True
        research_url = faculty_home_url + '/research/'
        sidenav += '<li><a href="/'+directory+'/research/">Research</a></li>\n'
    
    sidenav_output = open(directory + '/sidenav.inc', 'w+')
    sidenav_output.write(sidenav)
    sidenav_output.close()
    
    # Get faculty info
    faculty_page_match = page_contents_pattern.search(faculty_page_raw)
    if faculty_page_match:
        faculty_page_contents = faculty_page_match.group(1)
        home_output.write('<div>'+faculty_page_contents)
        home_output.close()
    
    # Get expert info
    if has_expert_page:
        # print "Found expert at " + expert_url
        expert_contents = get_page_contents(expert_url, 
                                            page_contents_pattern)
        if not os.path.exists(directory+'/expert/'):
            os.makedirs(directory+'/expert/')
        expert_output = open(directory+'/expert/index.pcf', 'w+')
        expert_output.write(expert_contents)
        expert_output.close()
        
    # Get research info
    if has_research_page:
        # print "Found research at " + research_url
        research_contents = get_page_contents(research_url, 
                                              page_contents_pattern)
        if not os.path.exists(directory+'/research/'):
            os.makedirs(directory+'/research/')
        research_output = open(directory+'/research/index.pcf', 'w+')
        research_output.write(research_contents)
        research_output.close()
    
    # Get publications info    
    if has_publications_page:
        # print "Found publications at " + publications_url
        publications_contents = get_page_contents(publications_url, 
                                                  page_contents_pattern)
        if not os.path.exists(directory+'/publications/'):
            os.makedirs(directory+'/publications/')
        publications_output = open(directory+'/publications/index.pcf', 'w+')
        publications_output.write(publications_contents)
        publications_output.close()
        
    #  Get course info
    if has_all_courses_page:
        # print "Found courses at " + courses_url
        try:
            all_courses_page = urllib2.urlopen(courses_url)
            all_courses_raw = all_courses_page.read()
            courses_page_contents = get_page_contents(courses_url, 
                                        courses_page_contents_pattern)
            if not os.path.exists(directory+'/courses/'):
                os.makedirs(directory+'/courses/')
            courses_output = open(directory+'/courses/index.pcf', 'w+')
            courses_output.write(courses_page_contents)
            courses_output.close()
            all_course_names = re.findall(course_name_pattern, 
                                          all_courses_raw)
            process_faculty_courses_page(faculty_home_url, 
                                         all_course_names,
                                         directory)
        except Exception as e:
            print "Unexpected error: " + str(e)
        
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
    except:
        print "147 Could not open page " + page_url

# Process all of the courses for one faculty
def process_faculty_courses_page(base_url, link_list, output_directory):
    sidenav = ""
    for course_name in link_list:
        course_url = base_url + "/courses/" + course_name + "/index.html"
        # print "Checking: " + course_name
        if (not(course_name.startswith('index.html')) 
                and (len(course_name)  >  0)):
            # print "Reading course: " + course_url
            sidenav_link = '/' + output_directory + '/courses/' + course_name + '/'
            sidenav += '<li><a href="'+sidenav_link+'">'+course_name+'</a></li>\n'
            
            course_contents = get_page_contents(
                                                course_url, 
                                                course_content_pattern)
            # print course_contents
            # print "Creating directory"
            course_directory = output_directory + '/courses/' + course_name
            # print "New course directory: " + course_directory
            if not os.path.exists(output_directory + '/courses/' + course_name):
                os.makedirs(output_directory + '/courses/' + course_name)
            course_output = open(output_directory + '/courses/' + course_name +'/index.pcf', 'w+')
            course_output.write(course_contents)
            course_output.close()
            
        else:
            print "Skipping course link: " + course_name
            
    sidenav_output = open(output_directory + '/courses/sidenav.inc', 'w+')
    sidenav_output.write(sidenav)
    sidenav_output.close()
    
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
