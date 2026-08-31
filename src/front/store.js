import { DEFAULT_CFG } from "../components/lumiAvatar"; // ajusta la ruta si difiere

export const initialStore = () => {
  return {
    message: null,
    // --- Acompañamiento / Citaciones ---
    students: [],
    studentsAlert: [],
    parentMeetings: [],

    // --- Actividades ---
    activities: [],
    allDetails: [],

    // --- Observaciones de clase ---
    classObservations: [],

    // --- Docentes y notificaciones ---
    teachers: [],
    notifications: [],
    myNotifications: [], // notificaciones que RECIBE el profe logueado

    // --- Planeaciones (PlanningCLIL) ---
    plannings: [],
    planReviews: [], // revisiones de coordinación (PLAN-*)

    // --- Currículo ---
    curriculumMaps: [],
    syllabusTemplates: [],
    primeMathMaps: [],
    neuroData: [],

    // --- Agenda / Retos / Recursos (Dashboard) ---
    weeklyChallenges: [],

    // --- Lumi ---
    lumiConfig: { ...DEFAULT_CFG },
    lumiName: "Lumi",

    // --- Demo boilerplate original ---
    todos: [
      { id: 1, title: "Make the bed", background: null },
      { id: 2, title: "Do my homework", background: null },
    ],
  };
};

export default function storeReducer(store, action = {}) {
  switch (action.type) {
    case "set_hello":
      return { ...store, message: action.payload };

    /* ============================================================
       STUDENTS ALERT (Acompañamiento)
       ============================================================ */
    case "set_students": {
      return { ...store, students: action.payload };
    }
    case "set_students_alert": {
      return { ...store, studentsAlert: action.payload };
    }
    case "add_student_global": {
      return { ...store, students: [action.payload, ...store.students] };
    }
    case "update_student_global": {
      return {
        ...store,
        students: store.students.map((s) =>
          s.ID_Student === action.payload.ID_Student
            ? { ...s, ...action.payload.patch }
            : s,
        ),
      };
    }
    case "remove_student_global": {
      return {
        ...store,
        students: store.students.filter((s) => s.ID_Student !== action.payload),
      };
    }

    /* ============================================================
       PARENT MEETINGS (Citaciones)
       ============================================================ */
    case "set_parent_meetings": {
      return { ...store, parentMeetings: action.payload };
    }
    case "add_parent_meeting": {
      return {
        ...store,
        parentMeetings: [action.payload, ...store.parentMeetings],
      };
    }

    /* ============================================================
       TEACHERS Y NOTIFICATIONS
       ============================================================ */
    case "set_teachers": {
      return { ...store, teachers: action.payload };
    }
    case "set_notifications": {
      return { ...store, notifications: action.payload };
    }
    case "add_notification": {
      return {
        ...store,
        notifications: [action.payload, ...store.notifications],
      };
    }
    case "mark_notification_read_global": {
      return {
        ...store,
        notifications: store.notifications.map((n) =>
          action.payload.includes(n.ID_Notification)
            ? { ...n, Status: "read" }
            : n,
        ),
      };
    }
    // Notificaciones que recibe el profe logueado (Dashboard/LumiCard)
    case "set_my_notifications": {
      return { ...store, myNotifications: action.payload };
    }
    case "mark_my_notifications_read": {
      return {
        ...store,
        myNotifications: store.myNotifications.map((n) =>
          action.payload.includes(n.ID_Notification)
            ? { ...n, Status: "read" }
            : n,
        ),
      };
    }

    /* ============================================================
       CLASS OBSERVATIONS
       ============================================================ */
    case "set_class_observations": {
      return { ...store, classObservations: action.payload };
    }
    case "upsert_class_observation": {
      const idx = store.classObservations.findIndex(
        (o) => String(o.ID_Lesson_Ref) === String(action.payload.ID_Lesson_Ref),
      );
      const updated = [...store.classObservations];
      if (idx >= 0) updated[idx] = action.payload;
      else updated.unshift(action.payload);
      return { ...store, classObservations: updated };
    }

    /* ============================================================
       ACTIVITIES + DETAILS
       ============================================================ */
    case "set_activities": {
      return { ...store, activities: action.payload };
    }
    case "update_activity_global": {
      return {
        ...store,
        activities: store.activities.map((a) =>
          a.ID_Activity === action.payload.ID_Activity
            ? { ...a, ...action.payload.patch }
            : a,
        ),
      };
    }
    case "set_all_details": {
      return { ...store, allDetails: action.payload };
    }
    case "upsert_activity_detail": {
      const idx = store.allDetails.findIndex(
        (d) => String(d.ID_Activity) === String(action.payload.ID_Activity),
      );
      const updated = [...store.allDetails];
      if (idx >= 0) updated[idx] = action.payload;
      else updated.push(action.payload);
      return { ...store, allDetails: updated };
    }

    /* ============================================================
       PLANNINGS (PlanningCLIL)
       ============================================================ */
    case "set_plannings": {
      return { ...store, plannings: action.payload };
    }
    case "add_plannings": {
      // Inserta N planeaciones nuevas al inicio (guardado optimista de Lumi)
      const incoming = Array.isArray(action.payload)
        ? action.payload
        : [action.payload];
      return { ...store, plannings: [...incoming, ...store.plannings] };
    }
    case "update_planning_global": {
      return {
        ...store,
        plannings: store.plannings.map((p) =>
          p.ID_Setup === action.payload.ID_Setup
            ? { ...p, ...action.payload.patch }
            : p,
        ),
      };
    }
    case "remove_planning_global": {
      return {
        ...store,
        plannings: store.plannings.filter((p) => p.ID_Setup !== action.payload),
      };
    }
    case "set_plan_reviews": {
      return { ...store, planReviews: action.payload };
    }
    case "upsert_plan_review": {
      const idx = store.planReviews.findIndex(
        (r) => String(r.ID_Lesson_Ref) === String(action.payload.ID_Lesson_Ref),
      );
      const updated = [...store.planReviews];
      if (idx >= 0) updated[idx] = action.payload;
      else updated.push(action.payload);
      return { ...store, planReviews: updated };
    }

    /* ============================================================
       CURRÍCULO (Maps / Syllabus / Prime / Neuro)
       ============================================================ */
    case "set_curriculum_maps": {
      return { ...store, curriculumMaps: action.payload };
    }
    case "set_syllabus_templates": {
      return { ...store, syllabusTemplates: action.payload };
    }
    case "set_prime_math_maps": {
      return { ...store, primeMathMaps: action.payload };
    }
    case "set_neuro_data": {
      return { ...store, neuroData: action.payload };
    }
    // Carga todo el currículo de una sola vez
    case "set_curriculum_all": {
      return {
        ...store,
        curriculumMaps: action.payload.maps ?? store.curriculumMaps,
        syllabusTemplates: action.payload.syll ?? store.syllabusTemplates,
        primeMathMaps: action.payload.prime ?? store.primeMathMaps,
      };
    }

    /* ============================================================
       WEEKLY CHALLENGES (Agenda / Retos / Recursos del Dashboard)
       ============================================================ */
    case "set_weekly_challenges": {
      return { ...store, weeklyChallenges: action.payload };
    }
    case "add_weekly_challenge": {
      return {
        ...store,
        weeklyChallenges: [...store.weeklyChallenges, action.payload],
      };
    }
    case "update_weekly_challenge": {
      return {
        ...store,
        weeklyChallenges: store.weeklyChallenges.map((c) =>
          c.ID_Challenge === action.payload.ID_Challenge
            ? { ...c, ...action.payload.patch }
            : c,
        ),
      };
    }
    case "remove_weekly_challenge": {
      return {
        ...store,
        weeklyChallenges: store.weeklyChallenges.filter(
          (c) => c.ID_Challenge !== action.payload,
        ),
      };
    }

    /* ============================================================
       LUMI
       ============================================================ */
    case "set_lumi_config": {
      return {
        ...store,
        lumiConfig: action.payload.config || store.lumiConfig,
        lumiName:
          action.payload.name !== undefined
            ? action.payload.name
            : store.lumiName,
      };
    }

    /* ============================================================
       DEMO BOILERPLATE
       ============================================================ */
    case "add_task": {
      const { id, color } = action.payload;
      return {
        ...store,
        todos: store.todos.map((todo) =>
          todo.id === id ? { ...todo, background: color } : todo,
        ),
      };
    }

    default:
      // Antes hacía throw Error → crasheaba la app entera.
      // Ahora si llega un action.type desconocido, avisamos y no rompemos.
      console.warn("Store: acción no reconocida →", action.type);
      return store;
  }
}
