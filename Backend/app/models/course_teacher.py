from sqlalchemy import Table, Column, Integer, ForeignKey
from .base import Base

# Association table for many-to-many relationship between Course and Teacher
course_teachers = Table(
    'course_teachers',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('teacher_id', Integer, ForeignKey('teachers.id'), primary_key=True)
) 