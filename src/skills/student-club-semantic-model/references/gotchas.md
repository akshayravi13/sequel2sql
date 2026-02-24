# Gotchas — student_club
1. **Many-to-Many Bridge Tables**: A student can be in multiple clubs. Always join through the `member_of` or `enrollment` table. Do not assume a 1-to-1 relationship.
