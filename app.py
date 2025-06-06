from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId
from dotenv import load_dotenv
import os
from datetime import datetime
from jinja2 import Environment
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
from auth import login_required, admin_required
from forms import RegistrationForm, LoginForm
from utils import allowed_file, save_uploaded_file, generate_avatar

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret-key-for-flash-messages")
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max
app.jinja_env.globals.update(now=datetime.now)

# Database connection setup
uri = os.getenv("MONGO_URI")
db_name = os.getenv("DB_NAME", "school_management")

try:
    client = MongoClient(uri)
    db = client[db_name]
    # Collections
    users_col = db['users']
    teachers_col = db['teachers']
    subjects_col = db['subjects']
    students_col = db['students']
    enrollments_col = db['enrollments']
    
    # Create indexes
    users_col.create_index('username', unique=True)
    teachers_col.create_index('email', unique=True)
    students_col.create_index('student_code', unique=True)
    subjects_col.create_index([('name', 1), ('group', 1), ('career', 1)], unique=True)
    
    # Test the connection
    client.admin.command('ping')
    db_status = {
        'connected': True,
        'last_check': datetime.now(),
        'server_info': client.server_info()
    }
    print("Successfully connected to MongoDB Atlas")
except ConnectionFailure as e:
    db_status = {
        'connected': False,
        'error': str(e),
        'last_check': datetime.now()
    }
    print("Error connecting to MongoDB Atlas")

# Context processor para inyectar db_status en todas las plantillas
@app.context_processor
def inject_db_status():
    return dict(db_status=db_status)

# Auth routes
from auth import auth_routes
app.register_blueprint(auth_routes)

@app.context_processor
def inject_collections():
    return dict(
        subjects_col=subjects_col,
        teachers_col=teachers_col,
        students_col=students_col,
        enrollments_col=enrollments_col
    )

@app.route('/')
@login_required
def dashboard():
    # Get stats for dashboard
    stats = {
        'teachers': teachers_col.count_documents({}),
        'students': students_col.count_documents({}),
        'subjects': subjects_col.count_documents({}),
        'enrollments': enrollments_col.count_documents({})
    }
    
    # Get recent activities con el conteo de materias
    recent_teachers = list(teachers_col.aggregate([
        {
            '$lookup': {
                'from': 'subjects',
                'localField': 'subject_ids',
                'foreignField': '_id',
                'as': 'subjects'
            }
        },
        {
            '$addFields': {
                'subject_count': {'$size': '$subjects'}
            }
        },
        {
            '$sort': {'_id': -1}
        },
        {
            '$limit': 5
        },
        {
            '$project': {
                'name': 1,
                'email': 1,
                'created_at': 1,
                'subject_count': 1
            }
        }
    ]))
    
    recent_students = list(students_col.find().sort('_id', -1).limit(5))
    recent_subjects = list(subjects_col.find().sort('_id', -1).limit(5))
    
    return render_template('dashboard.html', 
                         stats=stats,
                         recent_teachers=recent_teachers,
                         recent_students=recent_students,
                         recent_subjects=recent_subjects)

# Teachers routes
@app.route('/teachers')
@login_required
def show_teachers():
    teachers = list(teachers_col.aggregate([
        {
            '$lookup': {
                'from': 'subjects',
                'localField': 'subject_ids',
                'foreignField': '_id',
                'as': 'subjects'
            }
        }
    ]))
    return render_template('teachers/list.html', teachers=teachers)

@app.route('/teachers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_teacher():
    if request.method == 'POST':
        try:
            # Obtener y validar los IDs de materias
            subject_ids = []
            for subject_id in request.form.getlist('subjects'):
                try:
                    subject_ids.append(ObjectId(subject_id))
                except:
                    flash(f'ID de materia no válido: {subject_id}', 'danger')
                    return redirect(url_for('add_teacher'))
            
            # Validar que las materias existan
            for subject_id in subject_ids:
                if not subjects_col.find_one({'_id': subject_id}):
                    flash(f'Materia con ID {subject_id} no existe', 'danger')
                    return redirect(url_for('add_teacher'))
            
            # Manejar la carga de archivos
            photo_filename = None
            if 'photo' in request.files and request.files['photo'].filename != '':
                photo_filename = save_uploaded_file(
                    request.files['photo'], 
                    app.config['UPLOAD_FOLDER']
                )
            
            new_teacher = {
                'name': request.form['name'],
                'age': int(request.form['age']),
                'email': request.form['email'],
                'subject_ids': subject_ids,
                'titles': request.form.getlist('titles'),
                'photo': photo_filename,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            teachers_col.insert_one(new_teacher)
            flash('Profesor agregado exitosamente!', 'success')
            return redirect(url_for('show_teachers'))
        except Exception as e:
            flash(f'Error agregando profesor: {str(e)}', 'danger')
    
    subjects = list(subjects_col.find({}, {'name': 1}))
    return render_template('teachers/add.html', subjects=subjects)

@app.route('/teachers/edit/<teacher_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_teacher(teacher_id):
    teacher = teachers_col.find_one({'_id': ObjectId(teacher_id)})
    if not teacher:
        flash('Profesor no encontrado!', 'danger')
        return redirect(url_for('show_teachers'))
    
    if request.method == 'POST':
        try:
            subject_ids = []
            for subject_id in request.form.getlist('subjects'):
                try:
                    subject_ids.append(ObjectId(subject_id))
                except:
                    flash(f'ID de materia no válido: {subject_id}', 'danger')
                    return redirect(url_for('edit_teacher', teacher_id=teacher_id))
            
            update_data = {
                'name': request.form['name'],
                'age': int(request.form['age']),
                'email': request.form['email'],
                'subject_ids': subject_ids,
                'titles': request.form.getlist('titles'),
                'updated_at': datetime.now()
            }
            
            # Manejar la carga de archivos
            if 'photo' in request.files and request.files['photo'].filename != '':
                # Eliminar foto anterior si existe
                if teacher.get('photo'):
                    old_photo = os.path.join(app.config['UPLOAD_FOLDER'], teacher['photo'])
                    if os.path.exists(old_photo):
                        os.remove(old_photo)
                
                # Guardar nueva foto
                update_data['photo'] = save_uploaded_file(
                    request.files['photo'], 
                    app.config['UPLOAD_FOLDER']
                )
            
            teachers_col.update_one(
                {'_id': ObjectId(teacher_id)},
                {'$set': update_data}
            )
            flash('Profesor actualizado exitosamente!', 'success')
            return redirect(url_for('show_teachers'))
        except Exception as e:
            flash(f'Error actualizando profesor: {str(e)}', 'danger')
    
    subjects = list(subjects_col.find({}, {'name': 1}))
    return render_template('teachers/edit.html',
                         teacher=teacher,
                         subjects=subjects)

@app.route('/teachers/delete/<teacher_id>')
@login_required
@admin_required
def delete_teacher(teacher_id):
    try:
        teacher = teachers_col.find_one({'_id': ObjectId(teacher_id)})
        if teacher:
            # Delete photo if exists
            if teacher.get('photo'):
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], teacher['photo'])
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            
            # Remove teacher from subjects
            subjects_col.update_many(
                {'teacher_id': ObjectId(teacher_id)},
                {'$set': {'teacher_id': None}}
            )
            
            # Delete teacher
            result = teachers_col.delete_one({'_id': ObjectId(teacher_id)})
            if result.deleted_count > 0:
                flash('Teacher deleted successfully!', 'success')
            else:
                flash('Teacher not found!', 'warning')
        else:
            flash('Teacher not found!', 'warning')
    except Exception as e:
        flash(f'Error deleting teacher: {str(e)}', 'danger')
    return redirect(url_for('show_teachers'))

# Subjects routes
@app.route('/subjects')
@login_required
def show_subjects():
    subjects = list(subjects_col.aggregate([
        {
            '$lookup': {
                'from': 'teachers',
                'localField': 'teacher_id',
                'foreignField': '_id',
                'as': 'teacher'
            }
        },
        {
            '$unwind': {
                'path': '$teacher',
                'preserveNullAndEmptyArrays': True
            }
        },
        {
            '$project': {
                'name': 1,
                'schedule': 1,
                'credits': 1,
                'group': 1,
                'career': 1,
                'teacher': 1,
                'total_slots': 1,
                'available_slots': 1,
                '_id': 1
            }
        }
    ]))
    return render_template('subjects/list.html', subjects=subjects)

# Lista de carreras disponibles (puedes mover esto a la base de datos si lo prefieres)
CAREERS = [
    "Ingeniería de Sistemas",
    "Ingeniería Civil",
    "Medicina",
    "Derecho",
    "Administración de Empresas",
    "Psicología",
    "Arquitectura"
]

@app.route('/subjects/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_subject():
    if request.method == 'POST':
        try:
            new_subject = {
                'name': request.form['name'],
                'schedule': request.form['schedule'],
                'credits': int(request.form['credits']),
                'group': request.form['group'],
                'career': request.form['career'],
                'total_slots': int(request.form['total_slots']),
                'available_slots': int(request.form['total_slots']),
                'teacher_id': ObjectId(request.form['teacher']) if request.form['teacher'] else None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            result = subjects_col.insert_one(new_subject)
            flash('Materia agregada exitosamente!', 'success')
            return redirect(url_for('show_subjects'))
        except Exception as e:
            flash(f'Error agregando materia: {str(e)}', 'danger')
    
    teachers = list(teachers_col.find({}, {'name': 1, '_id': 1}))
    return render_template('subjects/add.html', 
                         teachers=teachers,
                         careers=CAREERS)

@app.route('/subjects/edit/<subject_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subject(subject_id):
    subject = subjects_col.find_one({'_id': ObjectId(subject_id)})
    if not subject:
        flash('Materia no encontrada!', 'danger')
        return redirect(url_for('show_subjects'))
    
    if request.method == 'POST':
        try:
            update_data = {
                'name': request.form['name'],
                'schedule': request.form['schedule'],
                'credits': int(request.form['credits']),
                'group': request.form['group'],
                'career': request.form['career'],
                'total_slots': int(request.form['total_slots']),
                'teacher_id': ObjectId(request.form['teacher']) if request.form['teacher'] else None,
                'updated_at': datetime.now()
            }
            
            subjects_col.update_one(
                {'_id': ObjectId(subject_id)},
                {'$set': update_data}
            )
            flash('Materia actualizada exitosamente!', 'success')
            return redirect(url_for('show_subjects'))
        except Exception as e:
            flash(f'Error actualizando materia: {str(e)}', 'danger')
    
    teachers = list(teachers_col.find({}, {'name': 1, '_id': 1}))
    return render_template('subjects/edit.html', 
                         subject=subject, 
                         teachers=teachers,
                         careers=CAREERS)

@app.route('/subjects/delete/<subject_id>')
@login_required
@admin_required
def delete_subject(subject_id):
    try:
        # Check if there are enrollments for this subject
        enrollments_count = enrollments_col.count_documents({'subject_id': ObjectId(subject_id)})
        if enrollments_count > 0:
            flash('Cannot delete subject with active enrollments!', 'danger')
            return redirect(url_for('show_subjects'))
        
        result = subjects_col.delete_one({'_id': ObjectId(subject_id)})
        if result.deleted_count > 0:
            flash('Subject deleted successfully!', 'success')
        else:
            flash('Subject not found!', 'warning')
    except Exception as e:
        flash(f'Error deleting subject: {str(e)}', 'danger')
    return redirect(url_for('show_subjects'))

# Students routes
@app.route('/students')
@login_required
def show_students():
    # Obtener estudiantes y contar sus matrículas
    students = list(students_col.find())
    
    # Agregar conteo de matrículas a cada estudiante
    for student in students:
        student['enrollments_count'] = enrollments_col.count_documents({'student_id': student['_id']})
    
    return render_template('students/list.html', students=students)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    if request.method == 'POST':
        try:
            photo_filename = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and allowed_file(file.filename):
                    photo_filename = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
            
            new_student = {
                'name': request.form['name'],
                'student_code': request.form['student_code'],
                'email': request.form['email'],
                'photo': photo_filename,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            result = students_col.insert_one(new_student)
            flash('Student added successfully!', 'success')
            return redirect(url_for('show_students'))
        except DuplicateKeyError:
            flash('A student with this code already exists!', 'danger')
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'danger')
    
    return render_template('students/add.html')

@app.route('/students/edit/<student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    student = students_col.find_one({'_id': ObjectId(student_id)})
    if not student:
        flash('Student not found!', 'danger')
        return redirect(url_for('show_students'))
    
    if request.method == 'POST':
        try:
            update_data = {
                'name': request.form['name'],
                'student_code': request.form['student_code'],
                'email': request.form['email'],
                'updated_at': datetime.now()
            }
            
            if 'photo' in request.files:
                file = request.files['photo']
                if file and allowed_file(file.filename):
                    # Delete old photo if exists
                    if student.get('photo'):
                        old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student['photo'])
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    # Save new photo
                    update_data['photo'] = save_uploaded_file(file, app.config['UPLOAD_FOLDER'])
            
            students_col.update_one(
                {'_id': ObjectId(student_id)},
                {'$set': update_data}
            )
            flash('Student updated successfully!', 'success')
            return redirect(url_for('show_students'))
        except Exception as e:
            flash(f'Error updating student: {str(e)}', 'danger')
    
    # Get student's enrollments with subject details
    enrollments = list(enrollments_col.aggregate([
        {'$match': {'student_id': ObjectId(student_id)}},
        {
            '$lookup': {
                'from': 'subjects',
                'localField': 'subject_id',
                'foreignField': '_id',
                'as': 'subject'
            }
        },
        {'$unwind': '$subject'}
    ]))
    
    # Calculate total credits
    total_credits = sum(enrollment['subject']['credits'] for enrollment in enrollments)
    
    # Get available subjects for enrollment
    available_subjects = list(subjects_col.aggregate([
        {
            '$match': {
                '_id': {'$nin': [e['subject_id'] for e in enrollments]},
                'available_slots': {'$gt': 0}
            }
        },
        {
            '$lookup': {
                'from': 'teachers',
                'localField': 'teacher_id',
                'foreignField': '_id',
                'as': 'teacher'
            }
        },
        {'$unwind': {'path': '$teacher', 'preserveNullAndEmptyArrays': True}}
    ]))
    
    return render_template('students/edit.html', 
                         student=student, 
                         enrollments=enrollments,
                         available_subjects=available_subjects,
                         total_credits=total_credits)

@app.route('/students/delete/<student_id>')
@login_required
@admin_required
def delete_student(student_id):
    try:
        student = students_col.find_one({'_id': ObjectId(student_id)})
        if student:
            # Delete photo if exists
            if student.get('photo'):
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student['photo'])
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            
            # Delete enrollments
            enrollments_col.delete_many({'student_id': ObjectId(student_id)})
            
            # Delete student
            result = students_col.delete_one({'_id': ObjectId(student_id)})
            if result.deleted_count > 0:
                flash('Student deleted successfully!', 'success')
            else:
                flash('Student not found!', 'warning')
        else:
            flash('Student not found!', 'warning')
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'danger')
    return redirect(url_for('show_students'))

# Enrollment routes
@app.route('/enroll/<student_id>/<subject_id>')
@login_required
@admin_required
def enroll_student(student_id, subject_id):
    try:
        # Check if student is already enrolled
        existing_enrollment = enrollments_col.find_one({
            'student_id': ObjectId(student_id),
            'subject_id': ObjectId(subject_id)
        })
        
        if existing_enrollment:
            flash('Student is already enrolled in this subject!', 'warning')
            return redirect(url_for('edit_student', student_id=student_id))
        
        # Get subject to check credits and available slots
        subject = subjects_col.find_one({'_id': ObjectId(subject_id)})
        if not subject:
            flash('Subject not found!', 'danger')
            return redirect(url_for('edit_student', student_id=student_id))
        
        # Check available slots
        if subject['available_slots'] <= 0:
            flash('No available slots in this subject!', 'danger')
            return redirect(url_for('edit_student', student_id=student_id))
        
        # Check student's total credits
        student_enrollments = list(enrollments_col.find({'student_id': ObjectId(student_id)}))
        enrolled_subjects = list(subjects_col.find({
            '_id': {'$in': [e['subject_id'] for e in student_enrollments]}
        }))
        
        total_credits = sum(subj['credits'] for subj in enrolled_subjects)
        if total_credits + subject['credits'] > 20:
            flash('Student cannot exceed 20 credits!', 'danger')
            return redirect(url_for('edit_student', student_id=student_id))
        
        # Create enrollment
        enrollment = {
            'student_id': ObjectId(student_id),
            'subject_id': ObjectId(subject_id),
            'enrollment_date': datetime.now()
        }
        
        # Start transaction
        with client.start_session() as session:
            with session.start_transaction():
                # Add enrollment
                enrollments_col.insert_one(enrollment, session=session)
                
                # Update available slots
                subjects_col.update_one(
                    {'_id': ObjectId(subject_id)},
                    {'$inc': {'available_slots': -1}},
                    session=session
                )
        
        flash('Student enrolled successfully!', 'success')
    except Exception as e:
        flash(f'Error enrolling student: {str(e)}', 'danger')
    
    return redirect(url_for('edit_student', student_id=student_id))

@app.route('/unenroll/<student_id>/<subject_id>')
@login_required
@admin_required
def unenroll_student(student_id, subject_id):
    try:
        # Start transaction
        with client.start_session() as session:
            with session.start_transaction():
                # Remove enrollment
                result = enrollments_col.delete_one({
                    'student_id': ObjectId(student_id),
                    'subject_id': ObjectId(subject_id)
                }, session=session)
                
                if result.deleted_count > 0:
                    # Update available slots
                    subjects_col.update_one(
                        {'_id': ObjectId(subject_id)},
                        {'$inc': {'available_slots': 1}},
                        session=session
                    )
                    flash('Student unenrolled successfully!', 'success')
                else:
                    flash('Enrollment not found!', 'warning')
    except Exception as e:
        flash(f'Error unenrolling student: {str(e)}', 'danger')
    
    return redirect(url_for('edit_student', student_id=student_id))

# Bulk import routes
@app.route('/import/teachers', methods=['GET', 'POST'])
@login_required
@admin_required
def import_teachers():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected!', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected!', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename, extensions={'json'}):
                data = json.load(file)
                
                if not isinstance(data, list):
                    flash('JSON file should contain an array of teachers!', 'danger')
                    return redirect(request.url)
                
                # Process each teacher
                inserted_count = 0
                for teacher_data in data:
                    try:
                        # Generate avatar if no photo provided
                        if not teacher_data.get('photo'):
                            teacher_data['photo'] = generate_avatar(teacher_data['name'])
                        
                        teacher_data['created_at'] = datetime.now()
                        teacher_data['updated_at'] = datetime.now()
                        
                        teachers_col.insert_one(teacher_data)
                        inserted_count += 1
                    except DuplicateKeyError:
                        continue
                    except Exception as e:
                        app.logger.error(f"Error importing teacher: {str(e)}")
                        continue
                
                flash(f'Successfully imported {inserted_count} teachers!', 'success')
                return redirect(url_for('show_teachers'))
            else:
                flash('Invalid file type! Only JSON files are allowed.', 'danger')
        except Exception as e:
            flash(f'Error importing teachers: {str(e)}', 'danger')
    
    return render_template('import/teachers.html')

@app.route('/import/subjects', methods=['GET', 'POST'])
@login_required
@admin_required
def import_subjects():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected!', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected!', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename, extensions={'json'}):
                data = json.load(file)
                
                if not isinstance(data, list):
                    flash('JSON file should contain an array of subjects!', 'danger')
                    return redirect(request.url)
                
                # Process each subject
                inserted_count = 0
                for subject_data in data:
                    try:
                        # Set teacher_id if provided
                        if subject_data.get('teacher_email'):
                            teacher = teachers_col.find_one({'email': subject_data['teacher_email']})
                            if teacher:
                                subject_data['teacher_id'] = teacher['_id']
                            del subject_data['teacher_email']
                        
                        subject_data['available_slots'] = subject_data['total_slots']
                        subject_data['created_at'] = datetime.now()
                        subject_data['updated_at'] = datetime.now()
                        
                        subjects_col.insert_one(subject_data)
                        inserted_count += 1
                    except Exception as e:
                        app.logger.error(f"Error importing subject: {str(e)}")
                        continue
                
                flash(f'Successfully imported {inserted_count} subjects!', 'success')
                return redirect(url_for('show_subjects'))
            else:
                flash('Invalid file type! Only JSON files are allowed.', 'danger')
        except Exception as e:
            flash(f'Error importing subjects: {str(e)}', 'danger')
    
    return render_template('import/subjects.html')

@app.route('/import/students', methods=['GET', 'POST'])
@login_required
@admin_required
def import_students():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected!', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected!', 'danger')
                return redirect(request.url)
            
            if file and allowed_file(file.filename, extensions={'json'}):
                data = json.load(file)
                
                if not isinstance(data, list):
                    flash('JSON file should contain an array of students!', 'danger')
                    return redirect(request.url)
                
                # Process each student
                inserted_count = 0
                for student_data in data:
                    try:
                        # Generate avatar if no photo provided
                        if not student_data.get('photo'):
                            student_data['photo'] = generate_avatar(student_data['name'])
                        
                        student_data['created_at'] = datetime.now()
                        student_data['updated_at'] = datetime.now()
                        
                        students_col.insert_one(student_data)
                        inserted_count += 1
                    except DuplicateKeyError:
                        continue
                    except Exception as e:
                        app.logger.error(f"Error importing student: {str(e)}")
                        continue
                
                flash(f'Successfully imported {inserted_count} students!', 'success')
                return redirect(url_for('show_students'))
            else:
                flash('Invalid file type! Only JSON files are allowed.', 'danger')
        except Exception as e:
            flash(f'Error importing students: {str(e)}', 'danger')
    
    return render_template('import/students.html')

# Reports and charts
@app.route('/reports')
@login_required
@admin_required
def reports():
    # Asegúrate que estas consultas devuelven datos
    subjects_by_career = list(subjects_col.aggregate([
        {'$group': {'_id': '$career', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}}
    ]))
    
    students_by_credits = list(enrollments_col.aggregate([
        {
            '$lookup': {
                'from': 'subjects',
                'localField': 'subject_id',
                'foreignField': '_id',
                'as': 'subject'
            }
        },
        {'$unwind': '$subject'},
        {
            '$group': {
                '_id': '$student_id',
                'total_credits': {'$sum': '$subject.credits'}
            }
        },
        {
            '$group': {
                '_id': {
                    '$switch': {
                        'branches': [
                            {'case': {'$lte': ['$total_credits', 10]}, 'then': '0-10'},
                            {'case': {'$lte': ['$total_credits', 15]}, 'then': '11-15'},
                            {'case': {'$lte': ['$total_credits', 20]}, 'then': '16-20'}
                        ],
                        'default': '20+'
                    }
                },
                'count': {'$sum': 1}
            }
        }
    ]))
    
    subjects_by_slots = list(subjects_col.aggregate([
        {
            '$group': {
                '_id': {
                    '$switch': {
                        'branches': [
                            {'case': {'$eq': ['$available_slots', 0]}, 'then': 'Full'},
                            {'case': {'$lte': ['$available_slots', 5]}, 'then': '1-5'},
                            {'case': {'$lte': ['$available_slots', 10]}, 'then': '6-10'},
                            {'case': {'$gt': ['$available_slots', 10]}, 'then': '10+'}
                        ],
                        'default': 'Unknown'
                    }
                },
                'count': {'$sum': 1}
            }
        }
    ]))
    
    return render_template('reports/index.html',
                         subjects_by_career=subjects_by_career,
                         students_by_credits=students_by_credits,
                         subjects_by_slots=subjects_by_slots)

@app.route('/database-info')
@login_required
@admin_required
def database_info():
    try:
        # Get active sessions
        sessions = list(client.admin.command('currentOp')['inprog'])
        # Get collection stats for each collection
        collections_stats = {
            'teachers': db.command('collstats', 'teachers'),
            'students': db.command('collstats', 'students'),
            'subjects': db.command('collstats', 'subjects'),
            'enrollments': db.command('collstats', 'enrollments')
        }
        # Get database stats
        db_stats = db.command('dbstats')
        
        return render_template('database_info.html',
                            sessions=sessions,
                            stats=collections_stats,
                            db_stats=db_stats,
                            db_status=db_status)
    except Exception as e:
        flash(f"Error obteniendo información de la base de datos: {str(e)}", "danger")
        return redirect(url_for('dashboard'))
    
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    # Registrar el error en la base de datos si está conectada
    if db_status.get('connected'):
        db.errors.insert_one({
            'error': str(e),
            'timestamp': datetime.now(),
            'type': '500'
        })
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)