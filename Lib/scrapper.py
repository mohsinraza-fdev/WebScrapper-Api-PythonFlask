from bs4 import BeautifulSoup
import requests
from flask import Flask
from flask import jsonify
import re
import csv

#app = Flask(__name__)

#@app.route('/')
#def index():
    #Converts tiem to 24 hour format
def convert(string_):
    if string_[-2:] == "AM" and string_[:2] == "12":
        return "00" + string_[2:-2]
    elif string_[-2:] == "AM":
        return string_[:-2]
    elif string_[-2:] == "PM" and string_[:2] == "12":
        return string_[:-2]
    else:
        return str(int(string_[:2]) + 12) + string_[2:5]


Id = 1
url = "https://www.marham.pk/doctors/karachi"
result = requests.get(url).text
doc = BeautifulSoup(result, "html.parser")
karachi_data = doc.find_all('div', class_= 'row mt-2 bg-white padding')[0]
spec_data = BeautifulSoup(str(karachi_data), 'html.parser')

#List off all the doctor specialities that exist in pakistan
spec_list = []
spec_name_data = spec_data.find_all('a')
for i in spec_name_data:
    spec_list.append(re.findall('(.*) in Karachi', i.string.strip())[0])

print('Specialities:\n'+str(spec_list)+'\n')

#Link Extensions of the specialites previously extracted in the same order
extension_list = []
links_data = spec_data.find_all('a', href=True)
for i in links_data:
    extension_list.append(re.findall('.*/(.*)', i['href'])[0])
print('Link Extensions:\n'+str(extension_list)+'\n')

link = 'https://www.marham.pk/doctors/karachi/'


GLOBAL_OUTPUT_LIST = []



for extension in extension_list:
    try:
        modified_link = link + extension
        print('\nNow Scrapping:' + modified_link)

        #modified_link = link+extension_list[2]
        value = requests.get(modified_link).text
        scrap_result = BeautifulSoup(value, 'html.parser')
        Dismissed = []


        LOCAL_OUTPUT_LIST = []



        count_per_page = 0
        page_no = 1
        save_page = page_no
        page_request = requests.get(modified_link+'?page='+str(page_no)).text
        for doctor in range(1, 21):
            DOCTOR = {}

            count_per_page += 1
            Dismiss = False
            #if count_per_page > 4:
            #    count_per_page = 1
            #    page_no += 1
            try:
                if save_page != page_no:
                    page_request = requests.get(modified_link+'?page='+str(page_no)).text
                    save_page = page_no

                doctor_scrapper = BeautifulSoup(page_request, 'html.parser')
                doctor_data = doctor_scrapper.find_all('div', attrs={'id': 'doctor-counter-'+str(count_per_page)})

                # From here doctor_data will get the card of doctor in each iteration
                #DOCTOR NAME EXTRACTION
                doctor_name_scrapper = BeautifulSoup(str(doctor_data[0]), 'html.parser')
                doctor_name = doctor_name_scrapper.find_all('h2', class_='font-size-md text-accent font-weight-bold mb-0 ga-event-listing-doctor-name mp-event-listing-doctor-name doctor-name')[0].string
                DOCTOR['name'] = str(doctor_name.strip())

                try:
                    #DOCTOR SPECIALIZATION EXTRACTION
                    doctor_specialization_scrapper = BeautifulSoup(str(doctor_data[0]), 'html.parser')
                    doctor_specialization = doctor_specialization_scrapper.find_all('p', class_='product-meta d-block font-size-sm mb-0')[0].string
                    DOCTOR['specialization'] = [ x.strip() for x in  str(doctor_specialization.strip()).split(',')]

                    #DOCTOR DESCRIPTION EXTRACTION
                    doctor_description_scrapper = BeautifulSoup(str(doctor_data[0]), 'html.parser')
                    doctor_description = doctor_description_scrapper.find_all('p', class_='mb-0 font-size-sm product-meta d-md-block d-none')[0].string
                    DOCTOR['description'] = str(doctor_description.strip())

                    #DOCTOR EXPERIENCE EXTRACTION
                    doctor_experience_scrapper = BeautifulSoup(str(doctor_data[0]), 'html.parser')
                    doctor_experience = doctor_experience_scrapper.find_all('p', class_='font-size-sm mb-0')[0].string
                    DOCTOR['experience'] = int(str(doctor_experience.strip()).split()[0])

                    #DOCTOR LOCATIONS EXTRACTION
                    doctor_locations_scrapper = BeautifulSoup(str(doctor_data[0]), 'html.parser')
                    doctor_locations = doctor_locations_scrapper.find_all('div', class_='ga-event-in-clinic-card-click')
                    location_list = []
                    unique_locations = []
                    for location_data in doctor_locations:
                        location = {}
                        location_data = str(location_data)
                        location_scrapper = BeautifulSoup(location_data, 'html.parser')

                        #LOCATION NAME EXTRACTION
                        location_name = location_scrapper.find_all('p', class_='font-size-xs mb-0 h3')[0].string
                        location['name'] = str(location_name.strip())

                        #LOCATION ADDRESS EXTRATION
                        location_latlong = location_scrapper.find_all('p', class_='product-meta d-block pb-1 mb-0 font-size-sm mx-2')[0].string
                        location['latlong'] = str(location_latlong.strip())

                        #LOCATION TIMING EXTRACTION
                        location_timing = location_scrapper.find_all('p', class_='mx-2 font-size-sm text-dark')[0].string
                        timing = [x.strip() for x in str(location_timing.strip()).split('-')]
                        location['timing'] = {'from': convert(timing[0]), 'to': convert(timing[1])}

                        #LOCATION DAYS EXTRACTION
                        location_days = location_scrapper.find_all('p', class_='mx-2 font-size-sm text-dark mb-0')[0].string
                        location['days'] = [x.strip() for x in str(location_days.strip()).split(',')]

                        location_list.append(location)

                    for unique_location in location_list:
                        if unique_location not in unique_locations:
                            unique_locations.append(unique_location)

                    DOCTOR['locations'] = sorted(unique_locations, key=lambda x: x['name'])

                except:
                    Dismiss = True

                #End the loop as soon as 1 doctor repeats
                if DOCTOR in LOCAL_OUTPUT_LIST:
                    break
                else:
                    if Dismiss == False:
                        LOCAL_OUTPUT_LIST.append(DOCTOR)
                        print('Doctor Considered: ' + str(DOCTOR['name']))

                    else:
                        x = str('\tDismissed Doctor: ' + str(DOCTOR['name']) + '\n\tPage Url: ' + str(modified_link))
                        if x in Dismissed:
                            break
                        else:
                            Dismissed.append(x)
                            print('\tDismissed Doctor: ' + str(DOCTOR['name']) + '\n\tPage Url: ' + str(modified_link+'?page='+str(page_no)))

            except:
                count_per_page = 0
                page_no += 1
                pass

        #Excluding the duplicate data and adding it to the final list of records
        for record in LOCAL_OUTPUT_LIST:
            if record not in GLOBAL_OUTPUT_LIST:
                GLOBAL_OUTPUT_LIST.append(record)
    except:
        print('Nothing Valuable Found...')
        pass
for finalized_doctor in GLOBAL_OUTPUT_LIST:
    finalized_doctor['id'] = str(Id).zfill(5)
    print(f'\n ID: {str(Id).zfill(5)} Allocated to ${str(finalized_doctor[str("name")])}')
    Id += 1

print(sorted(GLOBAL_OUTPUT_LIST, key=lambda x: x['experience']))
print('\nNumber of Unique Doctors Extracted: ' + str(len(GLOBAL_OUTPUT_LIST)))


# data = []
# for record in GLOBAL_OUTPUT_LIST:
#     for location in record['locations']:
#         raw = location['name'] + ' ' + location['latlong']
#         raw_data = {'Raw Data': raw, 'Name': '', 'Latlong': ''}
#         if raw_data not in data:
#             data.append(raw_data)
#
# header = ['Raw Data', 'Name', 'Latlong']
# with open('MapCoordinates.csv', 'w') as f:
#     writer = csv.DictWriter(f, fieldnames=header, lineterminator='\n')
#     writer.writeheader()
#     writer.writerows(data)

#    return {'data': GLOBAL_OUTPUT_LIST}
# format = {'Id': 'Generated', 'Name': 'Mr.x', 'Specializations': [1,2,3], 'Locations':[{'Name': 'Ziaudddin', 'Latlong': [123124, 352362], 'Timing': {'From': 'sdfsd', 'To': 'sdfsdgf'}, Days: []}],}

#if __name__ == '__main__':
#    app.run(debug=False, host='0.0.0.0')