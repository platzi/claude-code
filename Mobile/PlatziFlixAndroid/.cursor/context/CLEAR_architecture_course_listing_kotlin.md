# Arquitectura CLEAR en Kotlin/Jetpack Compose para la feature de listado de cursos

Este documento describe cómo se aplica la arquitectura **CLEAR** en una aplicación móvil desarrollada con **Kotlin** y **Jetpack Compose**, que actualmente cuenta con una única funcionalidad: **listar cursos**.

---

## 📁 Estructura del Proyecto

```plaintext
CourseLister/
│
├── Data/
│   ├── Entities/
│   │   └── CourseDTO.swift
│   ├── Mappers/
│   │   └── CourseMapper.swift
│   └── Repositories/
│       └── RemoteCourseRepository.swift
│
├── Domain/
│   ├── Models/
│   │   └── Course.swift
│   └── Repositories/
│       └── CourseRepository.swift (protocolo)
│
├── Presentation/
│   ├── ViewModels/
│   │   └── CourseListViewModel.swift
│   └── Views/
│       └── CourseListView.swift
