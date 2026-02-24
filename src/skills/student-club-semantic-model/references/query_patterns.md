-- Find Students in a Specific Club
SELECT s.first_name, s.last_name FROM student s JOIN member_of m ON s.student_id = m.student_id JOIN club c ON m.club_id = c.club_id WHERE c.club_name = {{club_name}};


-- EXTRA CANONICAL QUERIES

-- Clubs with declining membership
SELECT c.club_name, COUNT(m.student_id) as members, date_trunc('year', m.joined_at) as year
FROM club c JOIN member_of m ON c.club_id = m.club_id GROUP BY c.club_name, year ORDER BY c.club_name, year;
