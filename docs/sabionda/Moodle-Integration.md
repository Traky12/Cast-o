# Integración Moodle — Sabionda (GaiaChain)

**Objetivo**: Al completar un curso en Moodle, emitir certificado en GaiaChain vía backend CASTÚO.

---

## Flujo

1. **Moodle**: El alumno completa el curso → evento `course_completed` (o equivalente).
2. **Plugin Moodle / webhook**: Envía a backend CASTÚO `course_id`, `user_id`, `course_name`, `completion_date`.
3. **Backend**: Llama a `GaiaChainService` o al contrato `SabiondaCertificates.issueCertificate(courseName, studentId, studentName, completionDate)`.
4. **Respuesta**: Backend devuelve `tx_hash`; Moodle guarda enlace de verificación y muestra mensaje al alumno.

---

## Implementación Moodle (referencia)

```php
// moodle/local/gaiachain/lib.php (ejemplo)
function local_gaiachain_issue_certificate($courseid, $userid) {
    $student = get_user($userid);
    $course = get_course($courseid);
    $tx = gaiachain_issue_certificate(
        $course->fullname,
        $student->idnumber,
        $student->firstname . ' ' . $student->lastname,
        time()
    );
    return $tx;
}
```

---

## Seguridad y privacidad

- Minimizar datos personales en blockchain (studentId opaco, nombre según política).
- Autenticación del webhook (HMAC o API key) para que solo Moodle autorizado llame al backend.
