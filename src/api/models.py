from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, DateTime, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class Colegio(db.Model):
    __tablename__ = 'colegios'

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True)
    direccion: Mapped[str] = mapped_column(String(255), nullable=True)
    ciudad: Mapped[str] = mapped_column(String(100), nullable=True)
    telefono: Mapped[str] = mapped_column(String(50), nullable=True)
    email_contacto: Mapped[str] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users: Mapped[list["User"]] = relationship(
        "User", back_populates="colegio", cascade="all, delete-orphan")
    teachers_users: Mapped[list["TeachersUsers"]] = relationship(
        "TeachersUsers", back_populates="colegio", cascade="all, delete-orphan")
    lumi_config: Mapped[list["LumiConfig"]] = relationship(
        "LumiConfig", back_populates="colegio", cascade="all, delete-orphan")
    curriculum_maps: Mapped[list["CurriculumMaps"]] = relationship(
        "CurriculumMaps", back_populates="colegio", cascade="all, delete-orphan")
    syllabus_templates: Mapped[list["SyllabusTemplates"]] = relationship(
        "SyllabusTemplates", back_populates="colegio", cascade="all, delete-orphan")
    prime_math: Mapped[list["PrimeMath"]] = relationship(
        "PrimeMath", back_populates="colegio", cascade="all, delete-orphan")
    students_alert: Mapped[list["StudentsAlert"]] = relationship(
        "StudentsAlert", back_populates="colegio", cascade="all, delete-orphan")
    parent_meetings: Mapped[list["ParentMeetings"]] = relationship(
        "ParentMeetings", back_populates="colegio", cascade="all, delete-orphan")
    teacher_notifications: Mapped[list["TeacherNotifications"]] = relationship(
        "TeacherNotifications", back_populates="colegio", cascade="all, delete-orphan")
    neuro_stimulation: Mapped[list["NeuroStimulation"]] = relationship(
        "NeuroStimulation", back_populates="colegio", cascade="all, delete-orphan")
    lesson_planners: Mapped[list["LessonPlanners"]] = relationship(
        "LessonPlanners", back_populates="colegio", cascade="all, delete-orphan")
    logs_ia: Mapped[list["LogsIA"]] = relationship(
        "LogsIA", back_populates="colegio", cascade="all, delete-orphan")
    weekly_challenges: Mapped[list["WeeklyChallenges"]] = relationship(
        "WeeklyChallenges", back_populates="colegio", cascade="all, delete-orphan")
    activities_calendar: Mapped[list["ActivitiesCalendar"]] = relationship(
        "ActivitiesCalendar", back_populates="colegio", cascade="all, delete-orphan")
    class_observations: Mapped[list["ClassObservations"]] = relationship(
        "ClassObservations", back_populates="colegio", cascade="all, delete-orphan")
    activity_details_form: Mapped[list["ActivityDetailsForm"]] = relationship(
        "ActivityDetailsForm", back_populates="colegio", cascade="all, delete-orphan")

    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "ciudad": self.ciudad,
            "telefono": self.telefono,
            "email_contacto": self.email_contacto,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="users")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "email": self.email,
        }


class TeachersUsers(db.Model):
    __tablename__ = 'teachers_users'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    User_Key: Mapped[str] = mapped_column(String(100), nullable=False)
    Teacher_Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Assigned_Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Assigned_Subject: Mapped[str] = mapped_column(String(100), nullable=True)
    Total_Lessons: Mapped[int] = mapped_column(Integer, nullable=True)
    Password: Mapped[str] = mapped_column(String(255), nullable=False)
    ROL: Mapped[str] = mapped_column(String(50), nullable=False)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="teachers_users")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "User_Key": self.User_Key,
            "Teacher_Name": self.Teacher_Name,
            "Assigned_Grade": self.Assigned_Grade,
            "Assigned_Subject": self.Assigned_Subject,
            "Total_Lessons": self.Total_Lessons,
            "ROL": self.ROL
        }


class LumiConfig(db.Model):
    __tablename__ = 'lumi_config'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    Teacher_Key: Mapped[str] = mapped_column(String(100), nullable=False)
    Avatar_Style: Mapped[str] = mapped_column(String(100), nullable=True)
    Avatar_Seed: Mapped[str] = mapped_column(String(100), nullable=True)
    Avatar_Options_JSON: Mapped[str] = mapped_column(Text, nullable=True)
    Lumi_Name: Mapped[str] = mapped_column(String(100), nullable=True)
    Last_Updated: Mapped[str] = mapped_column(String(50), nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="lumi_config")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "Teacher_Key": self.Teacher_Key,
            "Avatar_Style": self.Avatar_Style,
            "Avatar_Seed": self.Avatar_Seed,
            "Avatar_Options_JSON": self.Avatar_Options_JSON,
            "Lumi_Name": self.Lumi_Name,
            "Last_Updated": self.Last_Updated
        }


class CurriculumMaps(db.Model):
    __tablename__ = 'curriculum_maps'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Map: Mapped[str] = mapped_column(String(100), nullable=False)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Subject: Mapped[str] = mapped_column(String(100), nullable=True)
    Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Term: Mapped[str] = mapped_column(String(50), nullable=True)
    Content_JSON: Mapped[str] = mapped_column(Text, nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="curriculum_maps")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Map": self.ID_Map,
            "Name": self.Name,
            "Subject": self.Subject,
            "Grade": self.Grade,
            "Term": self.Term,
            "Content_JSON": self.Content_JSON
        }


class SyllabusTemplates(db.Model):
    __tablename__ = 'syllabus_templates'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Syllabus: Mapped[str] = mapped_column(String(100), nullable=False)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Subject: Mapped[str] = mapped_column(String(100), nullable=True)
    Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Summary_JSON: Mapped[str] = mapped_column(Text, nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="syllabus_templates")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Syllabus": self.ID_Syllabus,
            "Name": self.Name,
            "Subject": self.Subject,
            "Grade": self.Grade,
            "Summary_JSON": self.Summary_JSON
        }


class PrimeMath(db.Model):
    __tablename__ = 'prime_math'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Map: Mapped[str] = mapped_column(String(100), nullable=False)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Subject: Mapped[str] = mapped_column(String(100), nullable=True)
    Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Term: Mapped[str] = mapped_column(String(50), nullable=True)
    Content_JSON: Mapped[str] = mapped_column(Text, nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="prime_math")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Map": self.ID_Map,
            "Name": self.Name,
            "Subject": self.Subject,
            "Grade": self.Grade,
            "Term": self.Term,
            "Content_JSON": self.Content_JSON
        }


class StudentsAlert(db.Model):
    __tablename__ = 'students_alert'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Student: Mapped[str] = mapped_column(String(100), nullable=False)
    Student_Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Entry_Date: Mapped[str] = mapped_column(String(50), nullable=True)
    Expected_MCER: Mapped[str] = mapped_column(String(50), nullable=True)
    Diagnostic_Result: Mapped[str] = mapped_column(String(100), nullable=True)
    Entry_Test_Richmond: Mapped[str] = mapped_column(
        String(100), nullable=True)
    # ← era String(100), lo subí a Text: guardas JSON aquí
    Assignments: Mapped[str] = mapped_column(Text, nullable=True)
    Observations: Mapped[str] = mapped_column(Text, nullable=True)
    Verdict: Mapped[str] = mapped_column(String(100), nullable=True)
    Term: Mapped[str] = mapped_column(String(50), nullable=True)
    Teacher_Key: Mapped[str] = mapped_column(String(100), nullable=True)
    Created_By: Mapped[str] = mapped_column(String(100), nullable=True)
    Last_Updated: Mapped[str] = mapped_column(String(50), nullable=True)
    Active: Mapped[str] = mapped_column(String(50), nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="students_alert")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Student": self.ID_Student,
            "Student_Name": self.Student_Name,
            "Grade": self.Grade,
            "Entry_Date": self.Entry_Date,
            "Expected_MCER": self.Expected_MCER,
            "Diagnostic_Result": self.Diagnostic_Result,
            "Entry_Test_Richmond": self.Entry_Test_Richmond,
            "Assignments": self.Assignments,
            "Observations": self.Observations,
            "Verdict": self.Verdict,
            "Term": self.Term,
            "Teacher_Key": self.Teacher_Key,
            "Created_By": self.Created_By,
            "Last_Updated": self.Last_Updated,
            "Active": self.Active
        }


class ParentMeetings(db.Model):
    __tablename__ = 'parent_meetings'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Meeting: Mapped[str] = mapped_column(String(100), nullable=False)
    ID_Student: Mapped[str] = mapped_column(String(100), nullable=True)
    Student_Name: Mapped[str] = mapped_column(String(255), nullable=True)
    Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Meeting_Reason: Mapped[str] = mapped_column(String(255), nullable=True)
    Meeting_Date: Mapped[str] = mapped_column(String(50), nullable=True)
    Attended: Mapped[str] = mapped_column(String(50), nullable=True)
    Commitment_Signed: Mapped[str] = mapped_column(String(50), nullable=True)
    Commitments: Mapped[str] = mapped_column(Text, nullable=True)
    Next_Followup: Mapped[str] = mapped_column(String(50), nullable=True)
    Responsible: Mapped[str] = mapped_column(String(100), nullable=True)
    Term: Mapped[str] = mapped_column(String(50), nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="parent_meetings")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Meeting": self.ID_Meeting,
            "ID_Student": self.ID_Student,
            "Student_Name": self.Student_Name,
            "Grade": self.Grade,
            "Meeting_Reason": self.Meeting_Reason,
            "Meeting_Date": self.Meeting_Date,
            "Attended": self.Attended,
            "Commitment_Signed": self.Commitment_Signed,
            "Commitments": self.Commitments,
            "Next_Followup": self.Next_Followup,
            "Responsible": self.Responsible,
            "Term": self.Term
        }


class TeacherNotifications(db.Model):
    __tablename__ = 'teacher_notifications'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Notification: Mapped[str] = mapped_column(String(100), nullable=False)
    Target_User_Key: Mapped[str] = mapped_column(String(100), nullable=True)
    Target_Teacher_Name: Mapped[str] = mapped_column(
        String(255), nullable=True)
    Message: Mapped[str] = mapped_column(Text, nullable=True)
    Sender: Mapped[str] = mapped_column(String(100), nullable=True)
    Status: Mapped[str] = mapped_column(String(50), nullable=True)
    Created_At: Mapped[str] = mapped_column(String(50), nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="teacher_notifications")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Notification": self.ID_Notification,
            "Target_User_Key": self.Target_User_Key,
            "Target_Teacher_Name": self.Target_Teacher_Name,
            "Message": self.Message,
            "Sender": self.Sender,
            "Status": self.Status,
            "Created_At": self.Created_At
        }


class NeuroStimulation(db.Model):
    __tablename__ = 'neuro_stimulation'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Neuro: Mapped[str] = mapped_column(String(100), nullable=False)
    Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Term: Mapped[str] = mapped_column(String(50), nullable=True)
    Week_Number: Mapped[str] = mapped_column(String(50), nullable=True)
    Day_of_Week: Mapped[str] = mapped_column(String(50), nullable=True)
    Target_Skill: Mapped[str] = mapped_column(String(100), nullable=True)
    Language: Mapped[str] = mapped_column(String(50), nullable=True)
    Activity_Type: Mapped[str] = mapped_column(String(100), nullable=True)
    Title_Activity: Mapped[str] = mapped_column(String(255), nullable=True)
    Instruction_Text: Mapped[str] = mapped_column(Text, nullable=True)
    Resource_Link: Mapped[str] = mapped_column(String(255), nullable=True)
    Extra_Data_JSON: Mapped[str] = mapped_column(Text, nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="neuro_stimulation")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Neuro": self.ID_Neuro,
            "Grade": self.Grade,
            "Term": self.Term,
            "Week_Number": self.Week_Number,
            "Day_of_Week": self.Day_of_Week,
            "Target_Skill": self.Target_Skill,
            "Language": self.Language,
            "Activity_Type": self.Activity_Type,
            "Title_Activity": self.Title_Activity,
            "Instruction_Text": self.Instruction_Text,
            "Resource_Link": self.Resource_Link,
            "Extra_Data_JSON": self.Extra_Data_JSON
        }


class LessonPlanners(db.Model):
    __tablename__ = 'lesson_planners'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Setup: Mapped[str] = mapped_column(String(100), nullable=False)
    Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Subject: Mapped[str] = mapped_column(String(100), nullable=True)
    Start_Date: Mapped[str] = mapped_column(String(50), nullable=True)
    Finish_Date: Mapped[str] = mapped_column(String(50), nullable=True)
    Term: Mapped[str] = mapped_column(String(50), nullable=True)
    Session_Number: Mapped[str] = mapped_column(String(50), nullable=True)
    Topic: Mapped[str] = mapped_column(String(255), nullable=True)
    Objective: Mapped[str] = mapped_column(Text, nullable=True)
    The_Hook: Mapped[str] = mapped_column(Text, nullable=True)
    Vocabulary: Mapped[str] = mapped_column(Text, nullable=True)
    # Vocabulary Big 5 puede pasar de 100
    Big_5: Mapped[str] = mapped_column(String(255), nullable=True)
    Thinking_Skill: Mapped[str] = mapped_column(String(255), nullable=True)
    Language_Frame: Mapped[str] = mapped_column(Text, nullable=True)
    Thinking_Routine: Mapped[str] = mapped_column(String(100), nullable=True)
    Richmond_Resources: Mapped[str] = mapped_column(String(255), nullable=True)
    Activity_Link: Mapped[str] = mapped_column(
        Text, nullable=True)  # varios links con coma
    Parent_Task: Mapped[str] = mapped_column(Text, nullable=True)
    Weekly_Challenge: Mapped[str] = mapped_column(Text, nullable=True)
    Percent_Status: Mapped[str] = mapped_column(String(50), nullable=True)
    TeacherSource: Mapped[str] = mapped_column(String(100), nullable=True)
    AI_Content_JSON: Mapped[str] = mapped_column(Text, nullable=True)
    ClassDojo_Link: Mapped[str] = mapped_column(String(255), nullable=True)
    Interactive_Feedback: Mapped[str] = mapped_column(Text, nullable=True)
    Feedback_Questions_JSON: Mapped[str] = mapped_column(Text, nullable=True)
    DBA_Reference: Mapped[str] = mapped_column(String(255), nullable=True)
    SDG_Connection: Mapped[str] = mapped_column(String(255), nullable=True)
    Assessment_Dimension: Mapped[str] = mapped_column(
        String(100), nullable=True)
    Evaluation_Instrument: Mapped[str] = mapped_column(
        String(100), nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="lesson_planners")

    def serialize(self):
        # El front usa claves con espacios ("The Hook", "Vocabulary Big 5", "Start Date"...)
        # Devolvemos AMBOS formatos para máxima compatibilidad con tus componentes.
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Setup": self.ID_Setup,
            "Grade": self.Grade,
            "Subject": self.Subject,
            "Term": self.Term,
            "Session_Number": self.Session_Number,
            "Topic": self.Topic,
            "Objective": self.Objective,
            "Thinking_Routine": self.Thinking_Routine,
            "Parent_Task": self.Parent_Task,
            "Weekly_Challenge": self.Weekly_Challenge,
            "Percent_Status": self.Percent_Status,
            "Teacher": self.TeacherSource,          # el front lee p.Teacher
            "Source": "Lumi" if (self.AI_Content_JSON and self.AI_Content_JSON.strip()) else "Manual",
            "AI_Content_JSON": self.AI_Content_JSON,
            "ClassDojo_Link": self.ClassDojo_Link,
            "Interactive_Feedback": self.Interactive_Feedback,
            "Feedback_Questions_JSON": self.Feedback_Questions_JSON,
            "DBA_Reference": self.DBA_Reference,
            "SDG_Connection": self.SDG_Connection,
            "Assessment_Dimension": self.Assessment_Dimension,
            "Evaluation_Instrument": self.Evaluation_Instrument,
            # --- Claves con espacios que espera el frontend ---
            "The Hook": self.The_Hook,
            "The_Hook": self.The_Hook,
            "Vocabulary Big 5": self.Big_5,
            "Vocabulary_Big_5": self.Big_5,
            "Thinking Skill": self.Thinking_Skill,
            "Language Frame": self.Language_Frame,
            "Thinking Routine": self.Thinking_Routine,
            "Richmond Resources": self.Richmond_Resources,
            "Richmond_Resources": self.Richmond_Resources,
            "Activity Link": self.Activity_Link,
            "Activity_Link": self.Activity_Link,
            "Parent Task": self.Parent_Task,
            "Weekly Challenge": self.Weekly_Challenge,
            "Start Date": self.Start_Date,
            "Start_Date": self.Start_Date,
            "Finish Date": self.Finish_Date,
            "Finish_Date": self.Finish_Date,
        }


class LogsIA(db.Model):
    __tablename__ = 'logs_ia'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    Fecha: Mapped[str] = mapped_column(String(50), nullable=True)
    Proveedor: Mapped[str] = mapped_column(String(100), nullable=True)
    Mensaje: Mapped[str] = mapped_column(Text, nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="logs_ia")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "Fecha": self.Fecha,
            "Proveedor": self.Proveedor,
            "Mensaje": self.Mensaje
        }


class WeeklyChallenges(db.Model):
    __tablename__ = 'weekly_challenges'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Challenge: Mapped[str] = mapped_column(String(100), nullable=False)
    Teacher_Key: Mapped[str] = mapped_column(String(100), nullable=True)
    Challenge_Description: Mapped[str] = mapped_column(Text, nullable=True)
    Start_Date: Mapped[str] = mapped_column(String(50), nullable=True)
    Days_Active: Mapped[str] = mapped_column(String(50), nullable=True)
    Status: Mapped[str] = mapped_column(String(50), nullable=True)
    Evidence_Note: Mapped[str] = mapped_column(Text, nullable=True)
    Bilingual_Resources: Mapped[str] = mapped_column(
        String(500), nullable=True)  # URLs largas

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="weekly_challenges")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Challenge": self.ID_Challenge,
            "Teacher_Key": self.Teacher_Key,
            "Challenge_Description": self.Challenge_Description,
            "Start_Date": self.Start_Date,
            "Days_Active": self.Days_Active,
            "Status": self.Status,
            "Evidence_Note": self.Evidence_Note,
            "Bilingual_Resources": self.Bilingual_Resources
        }


class ActivitiesCalendar(db.Model):
    __tablename__ = 'activities_calendar'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Activity: Mapped[str] = mapped_column(String(100), nullable=False)
    Event_Name: Mapped[str] = mapped_column(String(255), nullable=True)
    Responsable_ID: Mapped[str] = mapped_column(String(100), nullable=True)
    Status: Mapped[str] = mapped_column(String(50), nullable=True)
    Semaforo: Mapped[str] = mapped_column(String(50), nullable=True)
    Form_Status: Mapped[str] = mapped_column(String(50), nullable=True)
    Description: Mapped[str] = mapped_column(Text, nullable=True)
    Progress_Precent: Mapped[str] = mapped_column(String(50), nullable=True)
    Deadline: Mapped[str] = mapped_column(String(50), nullable=True)
    Final_Grade: Mapped[str] = mapped_column(String(50), nullable=True)
    Admin_Feedback: Mapped[str] = mapped_column(Text, nullable=True)
    Start: Mapped[str] = mapped_column(String(50), nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="activities_calendar")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Activity": self.ID_Activity,
            "Event_Name": self.Event_Name,
            "Responsable_ID": self.Responsable_ID,
            "Status": self.Status,
            "Semaforo": self.Semaforo,
            "Form_Status": self.Form_Status,
            "Description": self.Description,
            "Progress_Precent": self.Progress_Precent,
            "Deadline": self.Deadline,
            "Final_Grade": self.Final_Grade,
            "Admin_Feedback": self.Admin_Feedback,
            "Start": self.Start
        }


class ClassObservations(db.Model):
    __tablename__ = 'class_observations'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Lesson_Ref: Mapped[str] = mapped_column(String(100), nullable=False)
    Teacher_Name: Mapped[str] = mapped_column(
        String(255), nullable=True)   # ← AGREGADO
    Subject: Mapped[str] = mapped_column(
        String(100), nullable=True)        # ← AGREGADO
    Global_Score: Mapped[str] = mapped_column(
        String(50), nullable=True)    # ← AGREGADO
    Timing_Control: Mapped[str] = mapped_column(String(100), nullable=True)
    The_Hook_Check: Mapped[str] = mapped_column(String(100), nullable=True)
    Vocabulary_Focus: Mapped[str] = mapped_column(String(100), nullable=True)
    Scaffolding_Check: Mapped[str] = mapped_column(String(100), nullable=True)
    Student_Talk_Time: Mapped[str] = mapped_column(String(100), nullable=True)
    Thinking_Routine: Mapped[str] = mapped_column(String(100), nullable=True)
    Resource_Sync: Mapped[str] = mapped_column(String(100), nullable=True)
    Discipline_Flow: Mapped[str] = mapped_column(String(100), nullable=True)
    Goal_Achievement: Mapped[str] = mapped_column(String(100), nullable=True)
    Audio_Video_URL: Mapped[str] = mapped_column(String(255), nullable=True)
    Feedback: Mapped[str] = mapped_column(Text, nullable=True)
    Teacher: Mapped[str] = mapped_column(String(100), nullable=True)
    Grade: Mapped[str] = mapped_column(String(100), nullable=True)
    Score: Mapped[str] = mapped_column(String(50), nullable=True)
    Areas_for_Improvement: Mapped[str] = mapped_column(Text, nullable=True)
    Next_Steps: Mapped[str] = mapped_column(Text, nullable=True)
    Commitment: Mapped[str] = mapped_column(Text, nullable=True)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="class_observations")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Lesson_Ref": self.ID_Lesson_Ref,
            "Teacher_Name": self.Teacher_Name,
            "Subject": self.Subject,
            "Global_Score": self.Global_Score,
            "Timing_Control": self.Timing_Control,
            "The_Hook_Check": self.The_Hook_Check,
            "Vocabulary_Focus": self.Vocabulary_Focus,
            "Scaffolding_Check": self.Scaffolding_Check,
            "Student_Talk_Time": self.Student_Talk_Time,
            "Thinking_Routine": self.Thinking_Routine,
            "Resource_Sync": self.Resource_Sync,
            "Discipline_Flow": self.Discipline_Flow,
            "Goal_Achievement": self.Goal_Achievement,
            "Audio_Video_URL": self.Audio_Video_URL,
            "Feedback": self.Feedback,
            "Teacher": self.Teacher,
            "Grade": self.Grade,
            "Score": self.Score,
            "Areas_for_Improvement": self.Areas_for_Improvement,
            "Next_Steps": self.Next_Steps,
            "Commitment": self.Commitment,
            # Claves con espacios que usa ClassReview.jsx
            "Areas for Improvement": self.Areas_for_Improvement,
            "Next Steps": self.Next_Steps,
            "Feedback Action": self.Feedback,
            "Discipline & Flow": self.Discipline_Flow,
            "Audio/Video URL": self.Audio_Video_URL,
        }


class ActivityDetailsForm(db.Model):
    __tablename__ = 'activity_details_form'

    id: Mapped[int] = mapped_column(primary_key=True)
    colegio_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('colegios.id'), nullable=False)
    ID_Detail: Mapped[str] = mapped_column(String(100), nullable=False)
    ID_Activity: Mapped[str] = mapped_column(String(100), nullable=True)
    Academic_Objective: Mapped[str] = mapped_column(Text, nullable=True)
    Target_Vocabulary: Mapped[str] = mapped_column(Text, nullable=True)
    Language_Structures: Mapped[str] = mapped_column(Text, nullable=True)
    Speaking_Challenge: Mapped[str] = mapped_column(Text, nullable=True)
    Interactive_Stages: Mapped[str] = mapped_column(Text, nullable=True)
    Resource_Links: Mapped[str] = mapped_column(String(500), nullable=True)
    Evaluation_Method: Mapped[str] = mapped_column(String(100), nullable=True)
    Evidence_Preview: Mapped[str] = mapped_column(String(255), nullable=True)
    Budget_Status: Mapped[str] = mapped_column(String(50), nullable=True)
    Last_Updated: Mapped[str] = mapped_column(String(50), nullable=True)
    Feedback_Score: Mapped[str] = mapped_column(String(50), nullable=True)
    Feedback: Mapped[str] = mapped_column(
        Text, nullable=True)     # ← AGREGADO (lo usa tu POST)
    Score: Mapped[str] = mapped_column(
        String(50), nullable=True)  # ← AGREGADO (lo usa tu POST)

    colegio: Mapped["Colegio"] = relationship(
        "Colegio", back_populates="activity_details_form")

    def serialize(self):
        return {
            "id": self.id,
            "colegio_id": self.colegio_id,
            "ID_Detail": self.ID_Detail,
            "ID_Activity": self.ID_Activity,
            "Academic_Objective": self.Academic_Objective,
            "Target_Vocabulary": self.Target_Vocabulary,
            "Language_Structures": self.Language_Structures,
            "Speaking_Challenge": self.Speaking_Challenge,
            "Interactive_Stages": self.Interactive_Stages,
            "Resource_Links": self.Resource_Links,
            "Evaluation_Method": self.Evaluation_Method,
            "Evidence_Preview": self.Evidence_Preview,
            "Budget_Status": self.Budget_Status,
            "Last_Updated": self.Last_Updated,
            "Feedback_Score": self.Feedback_Score,
            "Feedback": self.Feedback,
            "Score": self.Score,
        }
