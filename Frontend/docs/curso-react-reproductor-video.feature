Feature: Visualización del reproductor de video en la primera clase del curso de React

  Como usuario de la plataforma
  Quiero acceder al curso de React y ver el reproductor de video en la primera clase
  Para poder consumir el contenido multimedia del curso

  Scenario: El usuario accede al curso de React y visualiza el reproductor de video en la primera clase
    Given el usuario está en la página principal "http://localhost:3000/"
    When el usuario selecciona el curso "Curso de React.js"
    And el usuario accede a la primera clase "Introducción a React"
    Then el usuario debería ver un reproductor de video en la página de la clase