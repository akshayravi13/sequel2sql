# Gotchas — codebase_community
1. **Post Types**: The `posts` table contains BOTH questions and answers. Filter by `PostTypeId` (1=Question, 2=Answer).
2. **Linking Answers to Questions**: An answer's `ParentId` points to the question's `Id`.
3. **Tags**: Stored as a concatenated string (e.g., `<python><sql>`) in `posts.Tags`. Use `LIKE '%<tag>%'`.
