CREATE TABLE `users` (
   `account` int NOT NULL AUTO_INCREMENT,
   `password` varchar(255) NOT NULL,
   `username` varchar(255) NOT NULL,
   `email` varchar(255) NOT NULL,
   `permission` varchar(255) NOT NULL,
   PRIMARY KEY (`account`)
 ) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


CREATE TABLE `students` (
   `student_id` int NOT NULL,
   `total_credits` int NOT NULL,
   PRIMARY KEY (`student_id`),
   CONSTRAINT `students_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`account`)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


CREATE TABLE `courses` (
   `course_id` int NOT NULL AUTO_INCREMENT,
   `course_name` varchar(255) NOT NULL,
   `credits` decimal(10,0) DEFAULT NULL,
   `teacher_account` int NOT NULL,
   PRIMARY KEY (`course_id`),
   KEY `teacher_account` (`teacher_account`),
   CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`teacher_account`) REFERENCES `users` (`account`)
 ) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


CREATE TABLE `course_selection` (
   `course_id` int NOT NULL,
   `student_id` int NOT NULL,
   KEY `course_id` (`course_id`),
   KEY `student_id` (`student_id`),
   CONSTRAINT `course_selection_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`),
   CONSTRAINT `course_selection_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `users` (`account`)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci


DELIMITER //
CREATE TRIGGER add_student_after_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    IF NEW.permission = 'student' THEN
        INSERT INTO students (student_id, total_credits) VALUES (NEW.account, 0);
    END IF;
END;
//
DELIMITER ;


DELIMITER //
CREATE PROCEDURE UpdateStudentTotalCredits (
    IN student_id INT
)
BEGIN
    DECLARE total_credits INT;

    -- 计算学生的总学分
    SELECT SUM(c.credits)
    INTO total_credits
    FROM course_selection cs
    JOIN courses c ON cs.course_id = c.course_id
    WHERE cs.student_id = student_id;

    -- 更新学生的总学分
    UPDATE students s
    SET total_credits = total_credits
    WHERE s.student_id = student_id;
END;
//
DELIMITER ;



DELIMITER $$
CREATE PROCEDURE update_total_credits()
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE student INT;
    -- 声明游标
    DECLARE student_cursor CURSOR FOR SELECT student_id FROM students;
    -- 声明处理游标结束的处理程序
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
    -- 打开游标
    OPEN student_cursor;
    -- 循环遍历游标中的每个学生
    read_loop: LOOP
        -- 从游标获取学生ID
        FETCH student_cursor INTO student;
        -- 如果到达游标末尾，则退出循环
        IF done THEN
            LEAVE read_loop;
        END IF;
        -- 计算学生的总学分
        UPDATE students s
        JOIN (
            SELECT cs.student_id, SUM(c.credits) AS total_credits
            FROM course_selection cs
            JOIN courses c ON cs.course_id = c.course_id
            WHERE cs.student_id = student
            GROUP BY cs.student_id
        ) subquery ON s.student_id = subquery.student_id
        SET s.total_credits = subquery.total_credits;
    END LOOP;
    -- 关闭游标
    CLOSE student_cursor;
END $$
DELIMITER ;






CREATE VIEW teachers AS
SELECT account, username, email, permission
FROM users
WHERE permission = 'teacher';



CREATE VIEW course_selection_info AS
SELECT
    cs.course_id,
    c.course_name,
    c.credits,
    cs.student_id,
    s.username AS student_name,
    s.email AS student_email,
    c.teacher_account,
    t.username AS teacher_name,
    t.email AS teacher_email
FROM
    course_selection cs
JOIN
    courses c ON cs.course_id = c.course_id
JOIN
    users s ON cs.student_id = s.account
JOIN
    users t ON c.teacher_account = t.account;
