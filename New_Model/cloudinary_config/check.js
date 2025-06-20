function requireLogin(req, res, next) {
  if (!req.session.user) return res.status(401).send('Please login first')
  next()
}

function requireRole(role) {
  return (req, res, next) => {
    if (!req.session.user || req.session.user.role !== role) {
      return res.status(403).send('Access denied')
    }
    next()
  }
}
app.get('/upload/job-description', requireRole('recruiter'), (req, res) => {
  res.send('Upload JD Page')
})
app.get('/upload/resume', requireRole('candidate'), (req, res) => {
  res.send('Upload Resume Page')
})
