import os
import pickle
import time
import requests
import pandas as pd
from datetime import date
from langchain.tools import tool
from src.utils import read_yaml

@tool
def get_available_specialites():
    '''use this tool to get available specialites'''
    response = requests.post('http://localhost:8000/doctor_info_json_format')
    doctor_information = pd.DataFrame(response.json())
    return list(doctor_information['speciality'].unique())

@tool
def get_available_dates(doctor_name, speciality):
    '''use this tool to get dates when a doctor is available. You need to give doctor name and speciality as input'''
    schedule_response = requests.post('http://localhost:8000/schedules_json_format')
    appointment_schedules = pd.DataFrame(schedule_response.json())    
    doctor_info_response = requests.post('http://localhost:8000/doctor_info_json_format')
    doctor_information = pd.DataFrame(doctor_info_response.json())
    earliest_timeslots = [] 
    doc_id = doctor_information[(doctor_information['doctor_name']==doctor_name) & \
                                (doctor_information['speciality']==speciality)]['doctor_id'].values[0]
    
    available_dates = sorted(set(appointment_schedules[(appointment_schedules['doctor_id']==doc_id) & \
                (appointment_schedules['status']=='Not Booked')]['available_date']))
    
    for date in available_dates:
        earliest_timeslots.append(min(list(appointment_schedules[(appointment_schedules['doctor_id']==doc_id) & \
            (appointment_schedules['available_date'] == date)& \
            (appointment_schedules['status']=='Not Booked')]['time_slot'])))
        
    return pd.DataFrame({'available_dates':available_dates,'earliest_timeslot': earliest_timeslots})

@tool
def get_doctor_timeslot(doctor_name, speciality,date):
    '''use this tool to list available time slots. \
    You need to give doctor name, speciality,and date but date is optional as input which should be in MM-DD-YYYY format.'''
    schedule_response = requests.post('http://localhost:8000/schedules_json_format')
    appointment_schedules = pd.DataFrame(schedule_response.json())    
    doctor_info_response = requests.post('http://localhost:8000/doctor_info_json_format')
    doctor_information = pd.DataFrame(doctor_info_response.json()) 
    doc_id = doctor_information[(doctor_information['doctor_name']==doctor_name) & \
                                (doctor_information['speciality']==speciality)]['doctor_id'].values[0]

    return list(appointment_schedules[(appointment_schedules['doctor_id']==doc_id) & \
                (appointment_schedules['status']=='Not Booked')&\
                (appointment_schedules['available_date']==date)]['time_slot'])
@tool
def book_appointment(patient_name, date_of_birth, doctor_name,speciality,date,time_slot):
    '''use this tool to book doctor appointment slot \
    you need to give patient_name,date_of_birth,doctor name, speciality,date in MM-DD-YYYY format,time_slot in HH:MM-to-HH:MM format as input
    '''
    schedule_response = requests.post('http://localhost:8000/schedules_json_format')
    appointment_schedules = pd.DataFrame(schedule_response.json())    
    doctor_info_response = requests.post('http://localhost:8000/doctor_info_json_format')
    doctor_information = pd.DataFrame(doctor_info_response.json())
    booked_slot_info_response = requests.post('http://localhost:8000/booked_slot_info_json_format')
    booked_slot_information = pd.DataFrame(booked_slot_info_response.json())
    patient_info_response = requests.post('http://localhost:8000/patient_info_json_format')
    patient_info_information = pd.DataFrame(patient_info_response.json())
    patient_contact = patient_info_information[(patient_info_information['Patient_Name']==patient_name) & \
                                        (patient_info_information['Patient_Date_of_Birth']==date_of_birth)]['Patient_PhoneNumber'].values[0]
    doc_id = doctor_information[(doctor_information['doctor_name']==doctor_name) & \
                                (doctor_information['speciality']==speciality)]['doctor_id'].values[0]
    
    updated_time_slot = time_slot.replace(' ','-')
    appointment_schedules.at[appointment_schedules[
                            (appointment_schedules['doctor_id']== doc_id) & \
                            (appointment_schedules['available_date']== date) & \
                            (appointment_schedules['status']=='Not Booked')& \
                            (appointment_schedules['time_slot']==updated_time_slot)].index[0],'status'] = "Booked"
    
    appointment_id = appointment_schedules[(appointment_schedules['doctor_id']== doc_id) & \
                            (appointment_schedules['available_date']== date) & \
                            (appointment_schedules['status']=='Booked')& \
                            (appointment_schedules['time_slot']==updated_time_slot)]['appointment_id'].values[0]
    
    patient_id = patient_info_information[(patient_info_information['Patient_Name']==patient_name) & (patient_info_information['Patient_Date_of_Birth']==date_of_birth)]['Patient_ID'].values[0]
    appointment_schedules_data = {'manipulated_data':appointment_schedules.to_dict(orient="records")}
    schedules_response = requests.post('http://localhost:8000/post-manipulated-schedules-data', json=appointment_schedules_data)
    booked_slot_information.loc[len(booked_slot_information)] = [appointment_id,doc_id,patient_id,updated_time_slot, date]
    data = {'manipulated_data':booked_slot_information.to_dict(orient='records')}
    response = requests.post('http://localhost:8000/post-manipulated-data', json=data)

    return f"{patient_name} your appointment with {doctor_name}, {speciality} is booked on {date} at {updated_time_slot}" 

@tool
def verify_existing_patient(patient_name,date_of_birth):
    '''use this tool to check if patient exists in our records or not \
    you need to give patient name, date of birth as input and date of birth input should be in YYYY-MM-DD format'''
    patient_info_response = requests.post('http://localhost:8000/patient_info_json_format')
    patient_info_information = pd.DataFrame(patient_info_response.json())
    check = patient_info_information[(patient_info_information["Patient_Name"]==patient_name) & \
                                (patient_info_information["Patient_Date_of_Birth"]==date_of_birth)].any(axis=None)
    return check

@tool
def update_coverage_info(patient_name,date_of_birth,member_id, member_name, insurance_plan,Relationship_with_Member):
    ''' use this tool to update patient insurance details \
        you need to give Patient Name, Date of Birth, Member ID, Member Name, Insurance Plan and Relationship with Member'''
    patient_info_response = requests.post('http://localhost:8000/patient_info_json_format')
    patient_info_information = pd.DataFrame(patient_info_response.json())
    patient_details = patient_info_information[(patient_info_information["Patient_Name"]==patient_name) & \
                                (patient_info_information["Patient_Date_of_Birth"]==date_of_birth)]
    patient_info_information.at[patient_info_information[
                            (patient_info_information["Patient_Name"]==patient_name) & \
                                (patient_info_information["Patient_Date_of_Birth"]==date_of_birth)].index[0],'Insurance_Plan'] = insurance_plan
    
    patient_info_information.at[patient_info_information[
                            (patient_info_information["Patient_Name"]==patient_name) & \
                                (patient_info_information["Patient_Date_of_Birth"]==date_of_birth)].index[0],'Member_ID'] = member_id
    
    patient_info_information.at[patient_info_information[
                            (patient_info_information["Patient_Name"]==patient_name) & \
                                (patient_info_information["Patient_Date_of_Birth"]==date_of_birth)].index[0],'Member_Name'] = member_name
    
    patient_info_information.at[patient_info_information[
                            (patient_info_information["Patient_Name"]==patient_name) & \
                                (patient_info_information["Patient_Date_of_Birth"]==date_of_birth)].index[0],'Relation_with_member'] = Relationship_with_Member
    
    data = {'manipulated_data':patient_info_information.to_dict(orient="records")}
    response = requests.post('http://localhost:8000/post-manipulated-patient-data', json=data)
    
    return f"{patient_name}, your coverage details are updated"

@tool
def add_new_patient(patient_name,date_of_birth,age,gender,email,phone_number,Insurance_Name,Insurance_Plan,Member_ID,Member_Name,Relation_with_member):
    '''Use this tool to add new patient details \
        you need to provide 4 following parameter \
        'patient_name','date_of_birth','age','gender','email', 'phone number',\
        'Insurance Name','Insurance Plan', 'Member ID', 'Member Name', and 'Relationship with Member' seperately as an input'''
        
    patient_info_response = requests.post('http://localhost:8000/patient_info_json_format')
    patient_info_information = pd.DataFrame(patient_info_response.json())
    no_of_pts = len(patient_info_information)
    patient_id = f'PT00{no_of_pts}'
    patient_info_information.loc[len(patient_info_information)] = [patient_id,patient_name, gender,date_of_birth, int(age),email,phone_number,Insurance_Plan,Member_ID,Member_Name,Relation_with_member,Insurance_Name]
    data = {'manipulated_data':patient_info_information.to_dict(orient="records")}
    response = requests.post('http://localhost:8000/post-manipulated-patient-data', json=data)
    return f'{patient_name}, you have been added to our records'

@tool
def get_coverage_info(patient_name,date_of_birth):
    ''' Use this tool to get insurance details of the patient. \
        you need to give patient name and date of birth as input'''
    patient_info_response = requests.post('http://localhost:8000/patient_info_json_format')
    patient_info_information = pd.DataFrame(patient_info_response.json())
    patient_details = patient_info_information[(patient_info_information["Patient_Name"]==patient_name) & \
                                (patient_info_information["Patient_Date_of_Birth"]==date_of_birth)]
    return patient_details[['Insurance_Name','Insurance_Plan','Member_ID','Member_Name','Relation_with_member']]

@tool
def get_doctor_using_speciality(speciality):
    '''use this tool to get doctor based on speciality \
    you need to give doctor speciality as input'''
    response = requests.post('http://localhost:8000/doctor_info_json_format')
    doctor_information = pd.DataFrame(response.json())
    return list(doctor_information[doctor_information['speciality']==speciality]['doctor_name'].unique())

@tool
def reschedule_patient_appointment(patient_name,date_of_birth,age,gender,doctor_name,speciality,time_slot,date):
    '''use this tool to reschedule patient appointment \
    you need to give patient name,date of birth,age,gender,doctor name,speciality,time slot,date as input'''
    updated_time_slot = time_slot.replace(' ','-')
    schedule_response = requests.post('http://localhost:8000/schedules_json_format')
    appointment_schedules = pd.DataFrame(schedule_response.json())
    patient_info_response = requests.post('http://localhost:8000/patient_info_json_format')
    patient_info_information = pd.DataFrame(patient_info_response.json())
    booked_slot_info_response = requests.post('http://localhost:8000/booked_slot_info_json_format')
    booked_slot_information = pd.DataFrame(booked_slot_info_response.json())
    doc_info_response = requests.post('http://localhost:8000/doctor_info_json_format')
    doctor_information = pd.DataFrame(doc_info_response.json())
    patient_id = patient_info_information[(patient_info_information['Patient_Name']==patient_name) & \
                                        (patient_info_information['Patient_Date_of_Birth']==date_of_birth)]['Patient_ID'].values[0]
    patient_contact = patient_info_information[(patient_info_information['Patient_Name']==patient_name) & \
                                        (patient_info_information['Patient_Date_of_Birth']==date_of_birth)]['Patient_PhoneNumber'].values[0]
    
    prev_appointment_id = booked_slot_information[booked_slot_information['patient_id']== patient_id]['appointment_id'].values[0]
    appointment_schedules.at[appointment_schedules[
                            (appointment_schedules['appointment_id']== prev_appointment_id)].index[0],'status'] = "Not Booked"
    
    doc_id = doctor_information[(doctor_information['doctor_name']==doctor_name) & \
                                (doctor_information['speciality']==speciality)]['doctor_id'].values[0]
    
    new_appointment_id = appointment_schedules[(appointment_schedules['time_slot']==updated_time_slot)&\
                                        (appointment_schedules['available_date']==date)&\
                                        (appointment_schedules['doctor_id']==doc_id)]['appointment_id'].values[0]
    
    appointment_schedules.at[appointment_schedules[
                            (appointment_schedules['appointment_id']== new_appointment_id) &\
                            (appointment_schedules['doctor_id']== doc_id) & \
                            (appointment_schedules['available_date']== date) & \
                            (appointment_schedules['status']=='Not Booked')& \
                            (appointment_schedules['time_slot']==updated_time_slot)].index[0],'status'] = "Booked"
    
    booked_slot_information.at[booked_slot_information[
                    (booked_slot_information['patient_id']==patient_id)].index[0],'appointment_id'] = new_appointment_id
    
    booked_slot_information.at[booked_slot_information[
                    (booked_slot_information['patient_id']==patient_id)].index[0],'alloted_time_slot'] = updated_time_slot
    
    booked_slot_information.at[booked_slot_information[
                    (booked_slot_information['patient_id']==patient_id)].index[0],'doctor_id'] = doc_id
    
    booked_slot_information.at[booked_slot_information[
                    (booked_slot_information['patient_id']==patient_id)].index[0],'alloted_date'] = date
    appointment_schedules_data = {'manipulated_data':appointment_schedules.to_dict(orient="records")}
    schedules_response = requests.post('http://localhost:8000/post-manipulated-schedules-data', json=appointment_schedules_data)

    data = {'manipulated_data':booked_slot_information.to_dict(orient="records")}
    response = requests.post('http://localhost:8000/post-manipulated-data', json=data)

    return f"{patient_name}, your appointment details have been updated"

@tool
def get_patient_appointment_details(patient_name,date_of_birth):
    ''' use this tool when you need to get patient appointment details. you need to use this tool in case of reschedule or cancellation \
        you need to give patient name and date of birth as input
    '''
    patient_info_response = requests.post('http://localhost:8000/patient_info_json_format')
    patient_info_information = pd.DataFrame(patient_info_response.json())
    booked_slot_info_response = requests.post('http://localhost:8000/booked_slot_info_json_format')
    booked_slot_information = pd.DataFrame(booked_slot_info_response.json())
    doc_info_response = requests.post('http://localhost:8000/doctor_info_json_format')
    doctor_information = pd.DataFrame(doc_info_response.json())
    
    patient_id = patient_info_information[(patient_info_information['Patient_Name']==patient_name) & \
                                        (patient_info_information['Patient_Date_of_Birth']==date_of_birth)]['Patient_ID'].values[0]
    patient_appointment_details = booked_slot_information[booked_slot_information['patient_id']== patient_id].tail(1)
    doc_id = patient_appointment_details['doctor_id'].values[0]
    alloted_time_slot = patient_appointment_details['alloted_time_slot'].values[0] 
    alloted_date = patient_appointment_details['alloted_date'].values[0]
    doctor_name = doctor_information[doctor_information['doctor_id']==doc_id]['doctor_name'].values[0]
    doctor_speciality = doctor_information[doctor_information['doctor_id']==doc_id]['speciality'].values[0]
    return f'{patient_name} has an appointment with {doctor_name}({doctor_speciality}) at {alloted_time_slot} on {alloted_date}'

@tool
def cancel_doctor_appointment(patient_name,date_of_birth,doctor_name,speciality):
    ''' use this tool to cancel the patient appointment scheduled with the doctor \
        you need to give patient name and date of birth as input'''

    schedule_response = requests.post('http://localhost:8000/schedules_json_format')
    appointment_schedules = pd.DataFrame(schedule_response.json())
    booked_slot_info_response = requests.post('http://localhost:8000/booked_slot_info_json_format')
    booked_slot_information = pd.DataFrame(booked_slot_info_response.json())
    patient_info_response = requests.post('http://localhost:8000/patient_info_json_format')
    patient_info_information = pd.DataFrame(patient_info_response.json())
    doc_info_response = requests.post('http://localhost:8000/doctor_info_json_format')
    doctor_information = pd.DataFrame(doc_info_response.json())
    
    patient_id = patient_info_information[(patient_info_information['Patient_Name']==patient_name) & \
                                        (patient_info_information['Patient_Date_of_Birth']==date_of_birth)]['Patient_ID'].values[0]
    patient_contact = patient_info_information[(patient_info_information['Patient_Name']==patient_name) & \
                                        (patient_info_information['Patient_Date_of_Birth']==date_of_birth)]['Patient_PhoneNumber'].values[0]
        
    doc_id = doctor_information[(doctor_information['doctor_name']==doctor_name) & \
                                (doctor_information['speciality']==speciality)]['doctor_id'].values[0]
    
    appointment_id = booked_slot_information[(booked_slot_information['patient_id']== patient_id) & \
                                            (booked_slot_information['doctor_id']== doc_id)]['appointment_id'].values[0]
    
    appointment_time_slot = booked_slot_information[(booked_slot_information['patient_id']== patient_id) & \
                                            (booked_slot_information['doctor_id']== doc_id)]['alloted_time_slot'].values[0]
    
    appointment_date = booked_slot_information[(booked_slot_information['patient_id']== patient_id) & \
                                            (booked_slot_information['doctor_id']== doc_id)]['alloted_date'].values[0]
    
    appointment_schedules.at[appointment_schedules[
                            (appointment_schedules['appointment_id']== appointment_id) & \
                            (appointment_schedules['doctor_id']== doc_id) & \
                            (appointment_schedules['available_date']==appointment_date)& \
                            (appointment_schedules['time_slot']==appointment_time_slot)].index[0],'status'] = "Not Booked"
    
    booked_slot_information = booked_slot_information[booked_slot_information['appointment_id'] != appointment_id]
    booked_slot_data = {'manipulated_data':booked_slot_information.to_dict(orient="records")}
    booked_slot_response = requests.post('http://localhost:8000/post-manipulated-data', json=booked_slot_data)
    
    appointment_schedules_data = {'manipulated_data':appointment_schedules.to_dict(orient="records")}
    schedules_response = requests.post('http://localhost:8000/post-manipulated-schedules-data', json=appointment_schedules_data)

    return f'{patient_name} your appointment with {doctor_name} at {appointment_time_slot} on {appointment_date} has been cancelled'

@tool
def get_current_date(query:str):
    ''' use this tool to know today's date
        example:- when patient says I am looking if doctor is available in next 3 days then get today's date and see for next 3 days'''
    today = date.today()
    return today.strftime("%m/%d/%y")
