"""
API Server: DB + endpoints.
Migrado de Google Apps Script a Flask + SQLAlchemy.
"""
from flask import Blueprint, request, jsonify
from api.models import (
    db, Colegio, User, TeachersUsers, LumiConfig, CurriculumMaps,
    SyllabusTemplates, PrimeMath, StudentsAlert, ParentMeetings,
    TeacherNotifications, NeuroStimulation, LessonPlanners, LogsIA,
    WeeklyChallenges, ActivitiesCalendar, ClassObservations, ActivityDetailsForm, LogsIA
)
from flask_cors import CORS
import json
from datetime import datetime

from api.ai_service import generate_with_fallback


api = Blueprint('api', __name__)
CORS(api)


# ==========================================
# HELPERS
# ==========================================
def now_iso():
    return datetime.utcnow().isoformat()


def gen_id(prefix):
    return f"{prefix}-{int(datetime.utcnow().timestamp() * 1000)}"


def get_colegio_id(data=None):
    """
    Resuelve el colegio del request.
    Prioridad: colegio_id en el body -> primer colegio de la BD (fallback single-tenant).
    Cuando agregues JWT, aquí lees el token y devuelves su colegio_id.
    """
    if data and data.get('colegio_id'):
        return data.get('colegio_id')
    first = Colegio.query.first()
    return first.id if first else None


# ==========================================
# HELLO / LOGIN
# ==========================================
@api.route('/hello', methods=['POST', 'GET'])
def handle_hello():
    return jsonify({"message": "Hello from the backend!"}), 200


@api.route('/login', methods=['POST'])
def login():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400

    user_key = body.get('user_key')
    password = body.get('password')
    if not user_key or not password:
        return jsonify({"status": "error", "message": "Usuario y contraseña requeridos"}), 400

    teacher = TeachersUsers.query.filter_by(User_Key=user_key).first()
    if teacher and teacher.Password == password:
        return jsonify({
            "status": "success",
            "message": "Login exitoso",
            "user": teacher.serialize(),
            "colegio": teacher.colegio.serialize() if teacher.colegio else None
        }), 200

    return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401


# ==========================================
# STUDENTS ALERT (Acompañamiento)
# ==========================================
@api.route('/students-alert', methods=['GET'])
def get_students_alert():
    term = request.args.get('term')
    try:
        query = StudentsAlert.query
        if term:
            query = query.filter_by(Term=term)
        return jsonify([s.serialize() for s in query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/students-alert', methods=['POST'])
def create_student_alert():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    try:
        new_student = StudentsAlert(
            colegio_id=get_colegio_id(data),
            ID_Student=data.get('ID_Student') or gen_id('STU'),
            Student_Name=data.get('Student_Name'),
            Grade=data.get('Grade'),
            Entry_Date=data.get('Entry_Date'),
            Expected_MCER=data.get('Expected_MCER'),
            Diagnostic_Result=data.get('Diagnostic_Result'),
            Entry_Test_Richmond=data.get('Entry_Test_Richmond'),
            Assignments=json.dumps(data.get('Assignments', [])),
            Observations=json.dumps(data.get('Observations', [])),
            Verdict=data.get('Verdict', ''),
            Term=data.get('Term'),
            Teacher_Key=data.get('Teacher_Key'),
            Created_By=data.get('Created_By', 'teacher'),
            Last_Updated=now_iso(),
            Active='TRUE'
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify({"status": "success", "id": new_student.ID_Student}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/students-alert/<string:id_student>/assignment', methods=['POST'])
def add_student_assignment(id_student):
    body = request.get_json(silent=True)
    text = body.get('text')
    if not text:
        return jsonify({"status": "error", "message": "El texto de la asignación es requerido"}), 400
    student = StudentsAlert.query.filter_by(ID_Student=id_student).first()
    if not student:
        return jsonify({"status": "error", "message": "Estudiante no encontrado"}), 404
    try:
        assignments = json.loads(
            student.Assignments) if student.Assignments else []
        if not isinstance(assignments, list):
            assignments = []
        assignments.append(
            {"id": gen_id('ASG'), "date": now_iso(), "text": text.strip()})
        student.Assignments = json.dumps(assignments)
        student.Last_Updated = now_iso()
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/students-alert/<string:id_student>/observation', methods=['POST'])
def add_student_observation(id_student):
    body = request.get_json(silent=True)
    text = body.get('text')
    author = body.get('author', '')
    if not text:
        return jsonify({"status": "error", "message": "El texto de la observación es requerido"}), 400
    student = StudentsAlert.query.filter_by(ID_Student=id_student).first()
    if not student:
        return jsonify({"status": "error", "message": "Estudiante no encontrado"}), 404
    try:
        observations = json.loads(
            student.Observations) if student.Observations else []
        if not isinstance(observations, list):
            observations = []
        observations.append(
            {"id": gen_id('OBS'), "date": now_iso(), "text": text.strip(), "author": author})
        student.Observations = json.dumps(observations)
        student.Last_Updated = now_iso()
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/students-alert/<string:id_student>/verdict', methods=['PUT', 'POST'])
def set_student_verdict(id_student):
    body = request.get_json(silent=True)
    verdict = body.get('verdict')
    student = StudentsAlert.query.filter_by(ID_Student=id_student).first()
    if not student:
        return jsonify({"status": "error", "message": "Estudiante no encontrado"}), 404
    try:
        student.Verdict = verdict
        student.Last_Updated = now_iso()
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/students-alert/<string:id_student>/active', methods=['PUT', 'POST'])
def toggle_student_active(id_student):
    body = request.get_json(silent=True)
    active_val = body.get('active', True)
    student = StudentsAlert.query.filter_by(ID_Student=id_student).first()
    if not student:
        return jsonify({"status": "error", "message": "Estudiante no encontrado"}), 404
    try:
        student.Active = 'TRUE' if active_val else 'FALSE'
        student.Last_Updated = now_iso()
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# PARENT MEETINGS (Citaciones)
# ==========================================
@api.route('/parent-meetings', methods=['GET'])
def get_parent_meetings():
    term = request.args.get('term')
    try:
        query = ParentMeetings.query
        if term:
            query = query.filter_by(Term=term)
        return jsonify([m.serialize() for m in query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/parent-meetings', methods=['POST'])
def create_parent_meeting():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    try:
        new_meeting = ParentMeetings(
            colegio_id=get_colegio_id(data),
            ID_Meeting=data.get('ID_Meeting') or gen_id('MTG'),
            ID_Student=data.get('ID_Student'),
            Student_Name=data.get('Student_Name'),
            Grade=data.get('Grade'),
            Meeting_Reason=data.get('Meeting_Reason'),
            Meeting_Date=data.get('Meeting_Date'),
            Attended=data.get('Attended'),
            Commitment_Signed=data.get('Commitment_Signed'),
            Commitments=data.get('Commitments'),
            Next_Followup=data.get('Next_Followup'),
            Responsible=data.get('Responsible'),
            Term=data.get('Term', 'Third Term')
        )
        db.session.add(new_meeting)
        db.session.commit()
        return jsonify({"status": "success", "data": new_meeting.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# ACTIVITIES CALENDAR + DETAILS
# ==========================================
@api.route('/activities-calendar', methods=['GET'])
def get_activities_calendar():
    try:
        activities = ActivitiesCalendar.query.all()
        return jsonify([a.serialize() for a in activities]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Alias que usa ActivitiesEvents.jsx: fetch(`${API_URL}/activities`)
@api.route('/activities', methods=['GET'])
def get_activities_alias():
    try:
        activities = ActivitiesCalendar.query.all()
        return jsonify([a.serialize() for a in activities]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Asignar responsable a una actividad (ActivitiesEvents "Tomar actividad")
@api.route('/activities/<string:id_activity>/assign', methods=['PUT'])
def assign_activity(id_activity):
    body = request.get_json(silent=True) or {}
    activity = ActivitiesCalendar.query.filter_by(
        ID_Activity=id_activity).first()
    if not activity:
        return jsonify({"status": "error", "message": "Actividad no encontrada"}), 404
    try:
        activity.Responsable_ID = body.get(
            'Responsable_ID', activity.Responsable_ID)
        db.session.commit()
        return jsonify({"status": "success", "data": activity.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/activity-details', methods=['GET'])
def get_activity_details():
    try:
        details = ActivityDetailsForm.query.all()
        return jsonify([d.serialize() for d in details]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Alias que usa ActivitiesEvents.jsx: fetch(`${API_URL}/activities-details`)
@api.route('/activities-details', methods=['GET'])
def get_activity_details_alias():
    try:
        details = ActivityDetailsForm.query.all()
        return jsonify([d.serialize() for d in details]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/activity-details', methods=['POST'])
@api.route('/activities-details', methods=['POST'])
def save_or_update_activity_detail():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    # Soporta payload envuelto en {action, data, rowId} o plano
    action_type = body.get('action', 'create')
    data = body.get('data', body)
    row_id = body.get('rowId')
    activity_id = data.get('ID_Activity')
    try:
        detail = None
        if action_type == 'update' and row_id:
            detail = ActivityDetailsForm.query.get(row_id)
        # Si no vino rowId pero ya existe detalle para esa actividad, actualízalo (upsert por ID_Activity)
        if not detail and activity_id:
            detail = (ActivityDetailsForm.query
                      .filter_by(ID_Activity=str(activity_id))
                      .order_by(ActivityDetailsForm.id.desc())
                      .first())

        if detail:
            detail.Academic_Objective = data.get(
                'Academic_Objective', detail.Academic_Objective)
            detail.Target_Vocabulary = data.get(
                'Target_Vocabulary', detail.Target_Vocabulary)
            detail.Language_Structures = data.get(
                'Language_Structures', detail.Language_Structures)
            detail.Speaking_Challenge = data.get(
                'Speaking_Challenge', detail.Speaking_Challenge)
            detail.Interactive_Stages = data.get(
                'Interactive_Stages', detail.Interactive_Stages)
            detail.Resource_Links = data.get(
                'Resource_Links', detail.Resource_Links)
            detail.Evaluation_Method = data.get(
                'Evaluation_Method', detail.Evaluation_Method)
            detail.Evidence_Preview = data.get(
                'Evidence_Preview', detail.Evidence_Preview)
            detail.Budget_Status = data.get(
                'Budget_Status', detail.Budget_Status)
            detail.Feedback = data.get('Feedback', detail.Feedback)
            detail.Score = data.get('Score', detail.Score)
            detail.Last_Updated = now_iso()
        else:
            detail = ActivityDetailsForm(
                colegio_id=get_colegio_id(data),
                ID_Activity=activity_id,
                ID_Detail=data.get('ID_Detail') or gen_id('DET'),
                Academic_Objective=data.get('Academic_Objective', ''),
                Target_Vocabulary=data.get('Target_Vocabulary', ''),
                Language_Structures=data.get('Language_Structures', ''),
                Speaking_Challenge=data.get('Speaking_Challenge', ''),
                Interactive_Stages=data.get('Interactive_Stages', ''),
                Resource_Links=data.get('Resource_Links', ''),
                Evaluation_Method=data.get('Evaluation_Method', ''),
                Evidence_Preview=data.get('Evidence_Preview', ''),
                Budget_Status=data.get('Budget_Status', 'Pending'),
                Feedback=data.get('Feedback', ''),
                Score=data.get('Score', ''),
                Last_Updated=now_iso()
            )
            db.session.add(detail)

        db.session.commit()
        return jsonify({"status": "success", "data": detail.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# CLASS OBSERVATIONS (Review + revisiones de planeación PLAN-)
# ==========================================
@api.route('/class-observations', methods=['GET'])
def get_class_observations():
    try:
        observations = ClassObservations.query.all()
        return jsonify([o.serialize() for o in observations]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/class-observations', methods=['POST'])
def save_or_update_class_observation():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    action_type = body.get('action', 'create')
    data = body.get('data', body)
    lesson_ref = body.get('idValue') or data.get('ID_Lesson_Ref')

    # Acepta claves con espacios y con guion bajo (ClassReview manda ambas)
    def pick(*keys, default=None):
        for k in keys:
            if k in data and data.get(k) not in (None, ''):
                return data.get(k)
        return default

    try:
        obs = None
        if lesson_ref:
            obs = ClassObservations.query.filter_by(
                ID_Lesson_Ref=lesson_ref).first()

        if action_type == 'update' and obs:
            pass  # cae al bloque de asignación de abajo
        elif not obs:
            obs = ClassObservations(
                colegio_id=get_colegio_id(data),
                ID_Lesson_Ref=lesson_ref or gen_id('REV')
            )
            db.session.add(obs)

        obs.Teacher_Name = pick('Teacher_Name', default=obs.Teacher_Name)
        obs.Teacher = pick('Teacher', default=obs.Teacher)
        obs.Grade = pick('Grade', default=obs.Grade)
        obs.Subject = pick('Subject', default=obs.Subject)
        obs.Timing_Control = pick(
            'Timing_Control', 'Timing Control', default=obs.Timing_Control or 0)
        obs.The_Hook_Check = pick(
            'The_Hook_Check', 'The Hook Check', default=obs.The_Hook_Check or 0)
        obs.Vocabulary_Focus = pick(
            'Vocabulary_Focus', 'Vocabulary Focus', default=obs.Vocabulary_Focus or 0)
        obs.Scaffolding_Check = pick(
            'Scaffolding_Check', 'Scaffolding Check', default=obs.Scaffolding_Check or 0)
        obs.Student_Talk_Time = pick(
            'Student_Talk_Time', 'Student Talk Time', default=obs.Student_Talk_Time or 0)
        obs.Thinking_Routine = pick(
            'Thinking_Routine', 'Thinking Routine', default=obs.Thinking_Routine or 0)
        obs.Resource_Sync = pick(
            'Resource_Sync', 'Resource Sync', default=obs.Resource_Sync or 0)
        obs.Discipline_Flow = pick(
            'Discipline_Flow', 'Discipline & Flow', default=obs.Discipline_Flow or 0)
        obs.Goal_Achievement = pick(
            'Goal_Achievement', 'Goal Achievement', default=obs.Goal_Achievement or 0)
        obs.Score = pick('Score', default=obs.Score or 0)
        obs.Global_Score = pick('Global_Score', default=obs.Global_Score or 0)
        obs.Audio_Video_URL = pick(
            'Audio_Video_URL', 'Audio/Video URL', default=obs.Audio_Video_URL)
        obs.Feedback = pick('Feedback', 'Feedback Action',
                            default=obs.Feedback)
        obs.Areas_for_Improvement = pick(
            'Areas_for_Improvement', 'Areas for Improvement', default=obs.Areas_for_Improvement)
        obs.Next_Steps = pick('Next_Steps', 'Next Steps',
                              default=obs.Next_Steps)
        obs.Commitment = pick('Commitment', default=obs.Commitment)

        db.session.commit()
        return jsonify({"status": "success", "data": obs.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# LUMI CONFIG
# ==========================================
@api.route('/lumi-config', methods=['GET'])
def get_lumi_config():
    teacher_key = request.args.get('teacher_key')
    try:
        query = LumiConfig.query
        if teacher_key:
            query = query.filter_by(Teacher_Key=teacher_key)
        return jsonify([c.serialize() for c in query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/lumi-config', methods=['POST'])
def save_lumi_config():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    teacher_key = data.get('Teacher_Key')
    if not teacher_key:
        return jsonify({"status": "error", "message": "Teacher_Key es requerido"}), 400
    try:
        config_record = LumiConfig.query.filter_by(
            Teacher_Key=teacher_key).first()
        if config_record:
            config_record.Avatar_Style = data.get(
                'Avatar_Style', config_record.Avatar_Style)
            config_record.Avatar_Seed = data.get(
                'Avatar_Seed', config_record.Avatar_Seed)
            config_record.Avatar_Options_JSON = data.get(
                'Avatar_Options_JSON', config_record.Avatar_Options_JSON)
            config_record.Lumi_Name = data.get(
                'Lumi_Name', config_record.Lumi_Name)
            config_record.Last_Updated = now_iso()
        else:
            config_record = LumiConfig(
                colegio_id=get_colegio_id(data),
                Teacher_Key=teacher_key,
                Avatar_Style=data.get('Avatar_Style', 'default'),
                Avatar_Seed=data.get('Avatar_Seed', 'Felix'),
                Avatar_Options_JSON=data.get('Avatar_Options_JSON', '{}'),
                Lumi_Name=data.get('Lumi_Name', 'Lumi'),
                Last_Updated=now_iso()
            )
            db.session.add(config_record)
        db.session.commit()
        return jsonify({"status": "success", "data": config_record.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# TEACHERS
# ==========================================
@api.route('/teachers-users', methods=['GET'])
def get_teachers_users():
    try:
        teachers = TeachersUsers.query.all()
        return jsonify({"status": "success", "data": [t.serialize() for t in teachers]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# TEACHER NOTIFICATIONS
# ==========================================
@api.route('/teacher-notifications', methods=['GET'])
def get_teacher_notifications():
    try:
        notifications = TeacherNotifications.query.all()
        return jsonify({"status": "success", "data": [n.serialize() for n in notifications]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/teacher-notifications', methods=['POST'])
def send_teacher_notification():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    target_user_key = data.get('Target_User_Key')
    message = data.get('Message')
    if not target_user_key or not message:
        return jsonify({"status": "error", "message": "Target_User_Key y Message son requeridos"}), 400
    try:
        new_notification = TeacherNotifications(
            colegio_id=get_colegio_id(data),
            ID_Notification=gen_id('NOT'),
            Target_User_Key=target_user_key,
            Target_Teacher_Name=data.get('Target_Teacher_Name', ''),
            Message=message,
            Sender=data.get('Sender', 'Coordinación'),
            Status='unread',
            Created_At=now_iso()
        )
        db.session.add(new_notification)
        db.session.commit()
        return jsonify({"status": "success", "data": new_notification.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/teacher-notifications/<string:notification_id>', methods=['PATCH'])
def update_notification_status(notification_id):
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    try:
        notification = TeacherNotifications.query.filter_by(
            ID_Notification=notification_id).first()
        if not notification:
            return jsonify({"status": "error", "message": "Notificación no encontrada"}), 404
        notification.Status = data.get('Status', notification.Status)
        db.session.commit()
        return jsonify({"status": "success", "data": notification.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# Marcar como leídas en lote (LumiCard llama a esto al abrir alertas)
@api.route('/teacher-notifications/mark-read', methods=['POST'])
def mark_notifications_read():
    body = request.get_json(silent=True) or {}
    ids = body.get('ids', [])
    if not isinstance(ids, list):
        return jsonify({"status": "error", "message": "ids debe ser una lista"}), 400
    try:
        for nid in ids:
            n = TeacherNotifications.query.filter_by(
                ID_Notification=nid).first()
            if n:
                n.Status = 'read'
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# LESSON PLANNERS  (el corazón de PlanningCLIL)
# ==========================================
@api.route('/lesson-planners', methods=['GET'])
def get_lesson_planners():
    term = request.args.get('term')
    teacher = request.args.get('teacher')
    try:
        query = LessonPlanners.query
        if term:
            query = query.filter_by(Term=term)
        if teacher:
            query = query.filter_by(Teacher=teacher)
        return jsonify([p.serialize() for p in query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def _apply_planner_fields(plan, data):
    """Copia los campos del payload (claves con espacio o guion) al modelo."""
    def g(*keys, default=None):
        for k in keys:
            if k in data and data.get(k) is not None:
                return data.get(k)
        return default

    plan.Grade = g('Grade', default=plan.Grade)
    plan.Subject = g('Subject', default=plan.Subject)
    plan.Term = g('Term', default=plan.Term)
    plan.Start_Date = g('Start Date', 'Start_Date', default=plan.Start_Date)
    plan.Finish_Date = g('Finish Date', 'Finish_Date',
                         default=plan.Finish_Date)
    plan.Session_Number = g('Session_Number', default=plan.Session_Number)
    plan.Topic = g('Topic', default=plan.Topic)
    plan.Objective = g('Objective', default=plan.Objective)
    plan.The_Hook = g('The Hook', 'The_Hook', default=plan.The_Hook)
    plan.Big_5 = g('Vocabulary Big 5', 'Vocabulary_Big_5', default=plan.Big_5)
    plan.Thinking_Skill = g(
        'Thinking Skill', 'Thinking_Skill', default=plan.Thinking_Skill)
    plan.Language_Frame = g(
        'Language Frame', 'Language_Frame', default=plan.Language_Frame)
    plan.Thinking_Routine = g(
        'Thinking Routine', 'Thinking_Routine', default=plan.Thinking_Routine)
    plan.Richmond_Resources = g(
        'Richmond Resources', 'Richmond_Resources', default=plan.Richmond_Resources)
    plan.Activity_Link = g(
        'Activity Link', 'Activity_Link', default=plan.Activity_Link)
    plan.Parent_Task = g('Parent Task', 'Parent_Task',
                         default=plan.Parent_Task)
    plan.Weekly_Challenge = g(
        'Weekly Challenge', 'Weekly_Challenge', default=plan.Weekly_Challenge)
    plan.Percent_Status = g('% Status', 'Percent_Status',
                            default=plan.Percent_Status)
    plan.Teacher = g('Teacher', 'TeacherSource', default=plan.Teacher)
    plan.AI_Content_JSON = g('AI_Content_JSON', default=plan.AI_Content_JSON)
    plan.ClassDojo_Link = g('ClassDojo_Link', default=plan.ClassDojo_Link)
    plan.Interactive_Feedback = g(
        'Interactive_Feedback', default=plan.Interactive_Feedback)
    plan.Feedback_Questions_JSON = g(
        'Feedback_Questions_JSON', default=plan.Feedback_Questions_JSON)
    plan.DBA_Reference = g('DBA_Reference', default=plan.DBA_Reference)
    plan.SDG_Connection = g('SDG_Connection', default=plan.SDG_Connection)
    plan.Assessment_Dimension = g(
        'Assessment_Dimension', default=plan.Assessment_Dimension)
    plan.Evaluation_Instrument = g(
        'Evaluation_Instrument', default=plan.Evaluation_Instrument)
    return plan


@api.route('/lesson-planners', methods=['POST'])
def create_lesson_planner():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    try:
        plan = LessonPlanners(
            colegio_id=get_colegio_id(data),
            ID_Setup=data.get('ID_Setup') or gen_id('AI')
        )
        _apply_planner_fields(plan, data)
        db.session.add(plan)
        db.session.commit()
        return jsonify({"status": "success", "data": plan.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/lesson-planners/<string:id_setup>', methods=['PUT'])
def update_lesson_planner(id_setup):
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    plan = LessonPlanners.query.filter_by(ID_Setup=id_setup).first()
    if not plan:
        return jsonify({"status": "error", "message": "Planeación no encontrada"}), 404
    try:
        _apply_planner_fields(plan, data)
        db.session.commit()
        return jsonify({"status": "success", "data": plan.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/lesson-planners/<string:id_setup>', methods=['DELETE'])
def delete_lesson_planner(id_setup):
    plan = LessonPlanners.query.filter_by(ID_Setup=id_setup).first()
    if not plan:
        return jsonify({"status": "error", "message": "Planeación no encontrada"}), 404
    try:
        db.session.delete(plan)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# WEEKLY CHALLENGES (Agenda + Recursos del Dashboard)
# ==========================================
@api.route('/weekly-challenges', methods=['GET'])
def get_weekly_challenges():
    teacher = request.args.get('teacher')
    try:
        query = WeeklyChallenges.query
        if teacher:
            query = query.filter_by(Teacher_Key=teacher)
        return jsonify([c.serialize() for c in query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/weekly-challenges', methods=['POST'])
def create_weekly_challenge():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    try:
        challenge = WeeklyChallenges(
            colegio_id=get_colegio_id(data),
            ID_Challenge=data.get('ID_Challenge') or gen_id('CH'),
            Teacher_Key=data.get('Teacher_Key'),
            Challenge_Description=data.get('Challenge_Description', ''),
            Start_Date=data.get('Start_Date', ''),
            Days_Active=data.get('Days_Active', ''),
            Status=data.get('Status', 'pending'),
            Evidence_Note=data.get('Evidence_Note', ''),
            Bilingual_Resources=data.get('Bilingual_Resources', '')
        )
        db.session.add(challenge)
        db.session.commit()
        return jsonify({"status": "success", "data": challenge.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/weekly-challenges/<string:id_challenge>', methods=['PUT'])
def update_weekly_challenge(id_challenge):
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400
    data = body.get('data', body)
    challenge = WeeklyChallenges.query.filter_by(
        ID_Challenge=id_challenge).first()
    if not challenge:
        return jsonify({"status": "error", "message": "Reto no encontrado"}), 404
    try:
        challenge.Teacher_Key = data.get('Teacher_Key', challenge.Teacher_Key)
        challenge.Challenge_Description = data.get(
            'Challenge_Description', challenge.Challenge_Description)
        challenge.Start_Date = data.get('Start_Date', challenge.Start_Date)
        challenge.Days_Active = data.get('Days_Active', challenge.Days_Active)
        challenge.Status = data.get('Status', challenge.Status)
        challenge.Evidence_Note = data.get(
            'Evidence_Note', challenge.Evidence_Note)
        challenge.Bilingual_Resources = data.get(
            'Bilingual_Resources', challenge.Bilingual_Resources)
        db.session.commit()
        return jsonify({"status": "success", "data": challenge.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/weekly-challenges/<string:id_challenge>', methods=['DELETE'])
def delete_weekly_challenge(id_challenge):
    challenge = WeeklyChallenges.query.filter_by(
        ID_Challenge=id_challenge).first()
    if not challenge:
        return jsonify({"status": "error", "message": "Reto no encontrado"}), 404
    try:
        db.session.delete(challenge)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# CURRICULUM: MAPS / SYLLABUS / PRIME MATH / NEURO
# ==========================================
@api.route('/curriculum-maps', methods=['GET'])
def get_curriculum_maps():
    try:
        return jsonify([m.serialize() for m in CurriculumMaps.query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/syllabus-templates', methods=['GET'])
def get_syllabus_templates():
    try:
        return jsonify([s.serialize() for s in SyllabusTemplates.query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/prime-math', methods=['GET'])
def get_prime_math():
    try:
        return jsonify([p.serialize() for p in PrimeMath.query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/neuro-stimulation', methods=['GET'])
def get_neuro_stimulation():
    grade = request.args.get('grade')
    term = request.args.get('term')
    try:
        query = NeuroStimulation.query
        if grade:
            query = query.filter_by(Grade=grade)
        if term:
            query = query.filter_by(Term=term)
        return jsonify([n.serialize() for n in query.all()]), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# IA - LUMI (placeholder Fase 2)
# ==========================================
# ==========================================
# IA - LUMI (fallback Groq -> Groq2 -> Gemini -> Mistral)
# ==========================================
@api.route('/generate-lumi', methods=['POST'])
def generate_lumi():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos en el body"}), 400

    prompt = body.get('prompt')
    if not prompt or not str(prompt).strip():
        return jsonify({"status": "error", "message": "El prompt es requerido"}), 400

    text, provider, errors = generate_with_fallback(prompt)

    # Registro opcional en LogsIA (no rompe si falla)
    try:
        log = LogsIA(
            colegio_id=get_colegio_id(body),
            Fecha=now_iso(),
            Proveedor=provider or "ninguno",
            Mensaje=("OK" if text else "; ".join(errors))[:2000]
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()

    if not text:
        return jsonify({
            "status": "error",
            "message": "Todos los proveedores de IA fallaron.",
            "detail": errors
        }), 502

    # El front espera { status, text } (lee data.text || data.raw)
    return jsonify({
        "status": "success",
        "text": text,
        "provider": provider
    }), 200


TABLE_REGISTRY = {
    "Curriculum_Maps":     CurriculumMaps,
    "Syllabus_Templates":  SyllabusTemplates,
    "Prime_Math":          PrimeMath,
    "Neuro_Stimulation":   NeuroStimulation,
    "Teachers_Users":      TeachersUsers,
    "Lesson_Planners":     LessonPlanners,
    "Students_Alert":      StudentsAlert,
    "Parent_Meetings":     ParentMeetings,
    "Teacher_Notifications": TeacherNotifications,
    "Weekly_Challenges":   WeeklyChallenges,
    "Activities_Calendar": ActivitiesCalendar,
    "Class_Observations":  ClassObservations,
    "Activity_Details_Form": ActivityDetailsForm,
    "Lumi_Config":         LumiConfig,
    "Logs_IA":             LogsIA,
}


def _editable_columns(model):
    """Columnas de la tabla que el usuario puede editar (excluye id y relaciones)."""
    cols = []
    for c in model.__table__.columns:
        if c.name in ('id',):
            continue
        cols.append(c.name)
    return cols

# ==========================================
# SUPER ADMIN — MINI EXCEL GENÉRICO
# ==========================================


@api.route('/admin/tables', methods=['GET'])
def list_tables():
    """Devuelve los nombres de tablas disponibles y sus columnas editables."""
    result = []
    for name, model in TABLE_REGISTRY.items():
        result.append({
            "name": name,
            "columns": _editable_columns(model)
        })
    return jsonify({"status": "success", "tables": result}), 200


@api.route('/admin/table/<string:table_name>', methods=['GET'])
def get_table_rows(table_name):
    """Devuelve todas las filas de una tabla, filtradas por colegio_id si se pasa."""
    model = TABLE_REGISTRY.get(table_name)
    if not model:
        return jsonify({"status": "error", "message": f"Tabla '{table_name}' no permitida"}), 400
    try:
        query = model.query
        colegio_id = request.args.get('colegio_id')
        # Filtra por empresa solo si el modelo tiene colegio_id
        if colegio_id and hasattr(model, 'colegio_id'):
            query = query.filter_by(colegio_id=colegio_id)
        rows = query.all()
        return jsonify({
            "status": "success",
            "columns": _editable_columns(model),
            "rows": [r.serialize() for r in rows]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/admin/table/<string:table_name>', methods=['POST'])
def append_table_rows(table_name):
    """
    Inserta filas nuevas (append) en la tabla.
    Body: { colegio_id, rows: [ {col: val, ...}, ... ] }
    """
    model = TABLE_REGISTRY.get(table_name)
    if not model:
        return jsonify({"status": "error", "message": f"Tabla '{table_name}' no permitida"}), 400

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    rows = body.get('rows', [])
    colegio_id = body.get('colegio_id') or get_colegio_id(body)
    if not isinstance(rows, list) or not rows:
        return jsonify({"status": "error", "message": "No hay filas para guardar"}), 400

    editable = set(_editable_columns(model))
    has_colegio = hasattr(model, 'colegio_id')

    created = 0
    try:
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            # Solo columnas válidas de la tabla; ignora lo que no exista
            clean_data = {k: v for k, v in raw.items() if k in editable}
            # Salta filas totalmente vacías
            if not any(str(v).strip() for v in clean_data.values() if v is not None):
                continue
            if has_colegio and not clean_data.get('colegio_id'):
                clean_data['colegio_id'] = colegio_id
            obj = model(**clean_data)
            db.session.add(obj)
            created += 1
        db.session.commit()
        return jsonify({"status": "success", "created": created}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/admin/table/<string:table_name>/<int:row_id>', methods=['DELETE'])
def delete_table_row(table_name, row_id):
    """Borra una fila puntual por su id."""
    model = TABLE_REGISTRY.get(table_name)
    if not model:
        return jsonify({"status": "error", "message": f"Tabla '{table_name}' no permitida"}), 400
    try:
        obj = model.query.get(row_id)
        if not obj:
            return jsonify({"status": "error", "message": "Fila no encontrada"}), 404
        db.session.delete(obj)
        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/admin/table/<string:table_name>/<int:row_id>', methods=['PUT'])
def update_table_row(table_name, row_id):
    """Edita una fila existente por su id."""
    model = TABLE_REGISTRY.get(table_name)
    if not model:
        return jsonify({"status": "error", "message": f"Tabla '{table_name}' no permitida"}), 400

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    data = body.get('data', body)
    editable = set(_editable_columns(model))

    try:
        obj = model.query.get(row_id)
        if not obj:
            return jsonify({"status": "error", "message": "Fila no encontrada"}), 404

        # Solo actualiza columnas válidas (ignora id y colegio_id para no romper la fila)
        for k, v in data.items():
            if k in editable and k not in ('id', 'colegio_id'):
                setattr(obj, k, v)

        db.session.commit()
        return jsonify({"status": "success", "data": obj.serialize()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# SUPER ADMIN — EMPRESAS
# ==========================================

@api.route('/admin/colegios', methods=['GET'])
def get_colegios():
    try:
        return jsonify({"status": "success", "data": [c.serialize() for c in Colegio.query.all()]}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api.route('/admin/colegios', methods=['POST'])
def create_colegio():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos"}), 400
    data = body.get('data', body)
    nombre = data.get('nombre')
    if not nombre or not nombre.strip():
        return jsonify({"status": "error", "message": "El nombre de la empresa es requerido"}), 400
    try:
        if Colegio.query.filter_by(nombre=nombre.strip()).first():
            return jsonify({"status": "error", "message": "Ya existe una empresa con ese nombre"}), 409
        colegio = Colegio(
            nombre=nombre.strip(),
            direccion=data.get('direccion'),
            ciudad=data.get('ciudad'),
            telefono=data.get('telefono'),
            email_contacto=data.get('email_contacto')
        )
        db.session.add(colegio)
        db.session.commit()
        return jsonify({"status": "success", "data": colegio.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# SUPER ADMIN — CREAR USUARIOS (Teachers_Users)
# ==========================================
@api.route('/admin/users', methods=['POST'])
def create_teacher_user():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Faltan datos"}), 400
    data = body.get('data', body)
    colegio_id = data.get('colegio_id') or get_colegio_id(data)
    if not colegio_id:
        return jsonify({"status": "error", "message": "Selecciona una empresa primero"}), 400

    user_key = data.get('User_Key')
    password = data.get('Password')
    name = data.get('Teacher_Name')
    if not user_key or not password or not name:
        return jsonify({"status": "error", "message": "User_Key, Password y Teacher_Name son requeridos"}), 400
    try:
        if TeachersUsers.query.filter_by(User_Key=user_key).first():
            return jsonify({"status": "error", "message": "Ese User_Key ya existe"}), 409
        teacher = TeachersUsers(
            colegio_id=colegio_id,
            User_Key=user_key,
            Teacher_Name=name,
            Assigned_Grade=data.get('Assigned_Grade', ''),
            Assigned_Subject=data.get('Assigned_Subject', ''),
            Total_Lessons=data.get('Total_Lessons') or 0,
            Password=password,   # ⚠️ sin hash por ahora (fase de pruebas)
            ROL=data.get('ROL', 'teacher')
        )
        db.session.add(teacher)
        db.session.commit()
        return jsonify({"status": "success", "data": teacher.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
