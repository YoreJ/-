from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection, transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.loader import get_template
from django.template.context_processors import csrf
from django.http import HttpResponse
from django.template import Context, loader
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def test(request):
    return HttpResponse("hello word!")


def login(request):
    return render(request, 'login.html')


def login_judge(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier')
        password = request.POST.get('password')

        # 获取数据库连接对象
        cursor = connection.cursor()
        # 查询数据库，检查用户名和密码是否匹配
        judge_sql = "SELECT * FROM users WHERE (username=%s OR email=%s) AND password=%s"
        cursor.execute(judge_sql, [identifier, identifier, password])
        result = cursor.fetchone()

        if result:
            # 登录成功，返回成功消息
            return render(request, 'loading.html', {'account': result[0]})
        else:
            # 登录失败，返回失败消息
            return render(request, 'error.html', {'error_string': '用户名或密码错误！'})
        # 连接到 MySQL 数据库

    else:
        return HttpResponse('The request method is not allowed!')


def create_account(request):
    return render(request, 'create_account.html')


def create_account_judge(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        user_type = request.POST['user_type']

        # 获取数据库连接对象
        cursor = connection.cursor()

        # 查询是否已存在相同邮箱的账户
        judge_sql = "SELECT * FROM users WHERE email=%s"
        cursor.execute(judge_sql, [email])
        result = cursor.fetchone()

        if result:
            return render(request, 'failure.html')
        else:
            # 在数据库中添加账户
            create_sql = ("INSERT INTO users (password, username, email, permission) "
                          "VALUES (%s, %s, %s, %s)")
            cursor.execute(create_sql, [password, username, email, user_type])
            # 获取刚刚插入的行的主键值（即 account）
            cursor.execute("SELECT LAST_INSERT_ID()")
            account = cursor.fetchone()[0]
            return render(request, 'loading.html', {'account': account})
    else:
        return render(request, 'create_account.html')


def system_interface(request, account):
    determine_account = "SELECT * FROM users WHERE account = %s"
    with connection.cursor() as cursor:
        cursor.execute(determine_account, [account])
        user = cursor.fetchone()

    if user[4] == 'student':
        select_courses_sql = ("SELECT cs.course_id, c.course_name, c.credits, u.username AS teacher_name "
                              "FROM course_selection AS cs "
                              "JOIN courses AS c ON cs.course_id = c.course_id "
                              "JOIN users AS u ON c.teacher_account = u.account "
                              "WHERE cs.student_id = %s")
        with connection.cursor() as student_cursor:
            student_cursor.execute(select_courses_sql, [user[0]])
            courses = student_cursor.fetchall()
        courses_list = [{'course_id': course[0], 'course_name': course[1], 'credits': float(course[2]), 'teacher_name': course[3]} for course in courses]
        courses_json = json.dumps(courses_list)
        select_feltered_courses = ("SELECT c.course_id, c.course_name, c.credits, u.username AS teacher_name "
                                   "FROM courses AS c "
                                   "JOIN users AS u ON c.teacher_account = u.account "
                                   "WHERE c.course_id NOT IN ("
                                   "SELECT cs.course_id "
                                   "FROM course_selection AS cs "
                                   "WHERE cs.student_id = %s)"
                                   )
        with connection.cursor() as course_cursor:
            course_cursor.execute(select_feltered_courses, [user[0]])
            filtered_courses = course_cursor.fetchall()
        all_courses = [{'course_id': course[0], 'course_name': course[1], 'credits': float(course[2]), 'teacher_name': course[3]} for course in filtered_courses]
        all_courses_json = json.dumps(all_courses)
        select_credits_sql = "SELECT total_credits FROM students WHERE student_id = %s"
        with connection.cursor() as student_cursor:
            student_cursor.execute(select_credits_sql, [user[0]])
            result = student_cursor.fetchone()  # 获取单个结果
            sum_credits = int(result[0]) if result and result[0] is not None else 0
        return render(request, 'student_success.html', {'courses_json': courses_json, 'all_courses_json': all_courses_json,
                                                        'student_id': user[0], 'student_password': user[1],
                                                        'student_name': user[2], 'student_email': user[3], 'sum_credits': sum_credits})
    elif user[4] == 'teacher':
        select_courses_sql = "SELECT * FROM courses WHERE teacher_account = %s"
        with connection.cursor() as teacher_cursor:
            teacher_cursor.execute(select_courses_sql, [user[0]])
            courses = teacher_cursor.fetchall()
        courses_list = [{'course_id': course[0], 'course_name': course[1], 'credits': float(course[2])} for course in courses]
        courses_json = json.dumps(courses_list)
        return render(request, 'teacher_success.html', {'courses_json': courses_json, 'teacher_id': user[0],
                                                        'teacher_password': user[1], 'teacher_name': user[2], 'teacher_email': user[3]})
    elif user[4] == 'admin':
        all_users_sql = "SELECT * FROM users"
        with connection.cursor() as admin_cursor:
            admin_cursor.execute(all_users_sql)
            users = admin_cursor.fetchall()
        users_list = [{'account': user[0], 'password': user[1], 'username': user[2], 'email': user[3], 'permission': user[4]} for user in users]
        users_json = json.dumps(users_list)

        all_courses_sql = ("SELECT c.course_id, c.course_name, c.credits, u.username AS teacher_name "
                           "FROM courses AS c "
                           "JOIN users AS u ON c.teacher_account = u.account")
        with connection.cursor() as admin_cursor:
            admin_cursor.execute(all_courses_sql)
            all_courses = admin_cursor.fetchall()
        all_courses_list = [{'course_id': course[0], 'course_name': course[1], 'credits': float(course[2]), 'teacher_name': course[3]} for course in all_courses]
        all_courses_json = json.dumps(all_courses_list)

        all_teachers_sql = "SELECT * FROM teachers"
        with connection.cursor() as admin_cursor:
            admin_cursor.execute(all_teachers_sql)
            teachers = admin_cursor.fetchall()
        teachers_list = [{'account':teacher[0], 'teacher_name': teacher[1]} for teacher in teachers]
        teachers_json = json.dumps(teachers_list)

        course_selection_sql = "SELECT * FROM course_selection_info"
        with connection.cursor() as admin_cursor:
            admin_cursor.execute(course_selection_sql)
            course_selections = admin_cursor.fetchall()
        course_selection_list = [{'course_id':course_selection[0], 'course_name':course_selection[1], 'credits':float(course_selection[2]), 
                                  'student_id':course_selection[3], 'student_name':course_selection[4], 'teacher_account':course_selection[6], 
                                  'teacher_name':course_selection[7]} for course_selection in course_selections]
        course_selection_json = json.dumps(course_selection_list)

        return render(request, 'admin_success.html', {'users_json': users_json, 'all_courses_json': all_courses_json, 'teachers_json': teachers_json, 'course_selection_json': course_selection_json,
                                                      'admin_id': user[0], 'admin_password': user[1], 'admin_name': user[2], 'admin_email': user[3]})
    else:
        return HttpResponse('非法类型！')


@csrf_exempt
def handle_data(request):
    if request.method == 'POST':
        # 获取表单数据
        data = request.POST
        action = data.get('action')

        if action == 'delete_course':
            course_id = data.get('course_id')
            account = data.get('account')
            delete_course_sql_1 = "DELETE FROM course_selection WHERE course_id = %s;"
            delete_course_sql_2 = "DELETE FROM courses WHERE course_id = %s;"
            update_credits_sql = "CALL update_total_credits();"

            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(delete_course_sql_1, [course_id])
                        cursor.execute(delete_course_sql_2, [course_id])
                        cursor.execute(update_credits_sql)
                return render(request, 'loading.html', {'account': account})
            except Exception as e:
                print(f"Error delete course: {e}")  # 打印错误信息用于调试
                return render(request, 'error.html', {'message': '删除课程时发生错误，请稍后再试。'})

        elif action == 'update_course':
            account = data.get('account')
            course_id = data.get('course_id')
            new_course_name = data.get('new_course_name')
            new_credits = data.get('new_credits')
            update_course_sql = "UPDATE courses SET course_name = %s, credits = %s WHERE course_id = %s"
            update_credits_sql = "CALL update_total_credits();"
            # 检查学分是否为数字
            if not new_credits.isdigit():
                return render(request, 'error.html', {'error_string': '学分必须为数字！', 'account': account})
            # 转换学分为浮点数类型
            new_credits = float(new_credits)
            # 检查学分是否为负值
            if new_credits <= 0:
                return render(request, 'error.html', {'error_string': '学分不能为非正数！', 'account': account})

            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(update_course_sql, [new_course_name, new_credits, course_id])
                        cursor.execute(update_credits_sql)
                return render(request, 'loading.html', {'account': account})
            except Exception as e:
                print(f"Error update course: {e}")  # 打印错误信息用于调试
                return render(request, 'error.html', {'message': '修改课程时发生错误，请稍后再试。'})

        elif action == 'add_course':
            adminId = data.get('admin_account')
            account = data.get('account')
            new_course_name = data.get('new_course_name')
            new_credits = data.get('new_credits')
            add_course_sql = "INSERT INTO courses (course_name, credits, teacher_account) VALUES (%s, %s, %s)"

            with connection.cursor() as cursor:
                cursor.execute(add_course_sql, [new_course_name, new_credits, account])
                connection.commit()
            if adminId:
                return render(request, 'loading.html', {'account': adminId})
            return render(request, 'loading.html', {'account': account})

        elif action == 'update_information':
            account = data.get('account')
            new_information = data.get('new_information')
            update_type = data.get('update_type')
            if update_type == '0':
                update_type = "user_name"
                update_teacher_sql = "UPDATE users SET username = %s WHERE account = %s"
                with connection.cursor() as cursor:
                    cursor.execute(update_teacher_sql, [new_information, account])
                return render(request, 'loading.html', {'account': account})
            elif update_type == '1':
                judge_email_sql = "SELECT * FROM users WHERE email = %s"
                with connection.cursor() as cursor:
                    cursor.execute(judge_email_sql, [new_information])
                result = cursor.fetchone()
                if result == None:
                    update_teacher_sql = "UPDATE users SET email = %s WHERE account = %s"
                    with connection.cursor() as cursor:
                        cursor.execute(update_teacher_sql, [new_information, account])
                    return render(request, 'loading.html', {'account': account})
                else:
                    return render(request, 'error.html', {'error_string': '该邮箱已经注册！', 'account': account})
            elif update_type == '2':
                update_teacher_sql = "UPDATE users SET password = %s WHERE account = %s"
                with connection.cursor() as cursor:
                    cursor.execute(update_teacher_sql, [new_information, account])
                return render(request, 'loading.html', {'account': account})


        elif action == 'select_course':
            course_id = data.get('course_id')
            account = data.get('account')

            insert_select_course_sql = "INSERT INTO course_selection (course_id, student_id) VALUES (%s, %s)"
            update_student_total_credits_proc = "CALL UpdateStudentTotalCredits(%s)"

            with connection.cursor() as cursor:
                # 插入选课记录
                cursor.execute(insert_select_course_sql, [course_id, account])
                # 调用存储过程更新学生总学分
                cursor.execute(update_student_total_credits_proc, [account])

            return render(request, 'loading.html', {'account': account})

        elif action == 'delete_student_course':
            adminId = data.get('admin_account')

            course_id = data.get('course_id')
            account = data.get('account')
            delete_select_course_sql = ("DELETE FROM course_selection "
                                        "WHERE course_id = %s")
            update_student_total_credits_proc = "CALL UpdateStudentTotalCredits(%s)"
            with connection.cursor() as cursor:
                cursor.execute(delete_select_course_sql, [course_id])
                cursor.execute(update_student_total_credits_proc, [account])

            if adminId:
                return render(request, 'loading.html', {'account': adminId})

            return render(request, 'loading.html', {'account': account})

        elif action == 'enter_user':
            email = data.get('email')
            get_account_sql = "SELECT account FROM users WHERE email = %s"
            with connection.cursor() as cursor:
                cursor.execute(get_account_sql, [email])
                account = cursor.fetchall()[0][0]
            return render(request, 'loading.html', {'account': account})

        elif action == 'delete_user':
            email = data.get('email')
            admin_account = data.get('account')
            permission = data.get('permission')
            if permission == 'teacher':
                select_account_sql = "SELECT account INTO @teacher_account FROM users WHERE email = %s;"
                delete_course_selection_sql = ("DELETE FROM course_selection "
                                               "WHERE course_id IN "
                                               "(SELECT course_id FROM courses "
                                               "WHERE teacher_account = @teacher_account);")
                delete_course_sql = "DELETE FROM courses WHERE teacher_account = @teacher_account;"
                delete_user_sql = "DELETE FROM users WHERE account = @teacher_account;"
                with connection.cursor() as cursor:
                    cursor.execute(select_account_sql, [email])
                    cursor.execute(delete_course_selection_sql)
                    cursor.execute(delete_course_sql)
                    cursor.execute(delete_user_sql)
                connection.commit()
            elif permission == 'student':
                select_account_sql = "SELECT account INTO @student_account FROM users WHERE email = %s;"
                delete_course_selection_sql = "DELETE FROM course_selection WHERE student_id = @student_account;"
                delete_student_sql = "DELETE FROM students WHERE student_id = @student_account;"
                delete_user_sql = "DELETE FROM users WHERE account = @student_account;"
                with connection.cursor() as cursor:
                    cursor.execute(select_account_sql, [email])
                    cursor.execute(delete_course_selection_sql)
                    cursor.execute(delete_student_sql)
                    cursor.execute(delete_user_sql)
                connection.commit()
            else:
                return render(request, 'failure.html')
            return render(request, 'loading.html', {'account': admin_account})

        elif action == 'add_user':
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            permission = data.get('permission')
            account = data.get('account')
            cursor = connection.cursor()
            # 查询是否已存在相同邮箱的账户
            judge_sql = "SELECT * FROM users WHERE email=%s"
            cursor.execute(judge_sql, [email])
            result = cursor.fetchone()
            if result:
                return render(request, 'error.html', {'error_string': '该邮箱已经注册！', 'account': account})
            elif not password:
                return render(request, 'error.html', {'error_string': '密码不能为空！', 'account': account})
            elif not username:
                return render(request, 'error.html', {'error_string': '用户名不能为空！', 'account': account})
            elif not email:
                return render(request, 'error.html', {'error_string': '邮箱不能为空！', 'account': account})
            else:
                create_sql = ("INSERT INTO users (password, username, email, permission) "
                              "VALUES (%s, %s, %s, %s)")
                cursor.execute(create_sql, [password, username, email, permission])
                return render(request, 'loading.html', {'account': account})

        else:
            return render(request, 'error.html', {'error_string': '类型非法！'})