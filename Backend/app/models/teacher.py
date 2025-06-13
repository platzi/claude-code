from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import BaseModel


class Teacher(BaseModel):
    """
    Teacher model representing instructors for courses.
    """
    __tablename__ = 'teachers'
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    
    # Many-to-many relationship with Course
    courses = relationship(
        "Course", 
        secondary="course_teachers", 
        back_populates="teachers"
    )
    
    def __repr__(self):
        return f"<Teacher(id={self.id}, name='{self.name}', email='{self.email}')>" 