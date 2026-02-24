-- Club Membership Count
SELECT club_name, COUNT(student_id) FROM club JOIN member_of ON club.club_id = member_of.club_id GROUP BY club_name;
