app.post('/upload/resume/:company', upload.single('file'), async (req, res) => {
  const company = req.params.company;

  try {
    const result = await cloudinary.uploader.upload(req.file.path, {
      resource_type: 'raw',
      folder: `${company}/resumes`       // e.g., CompanyA/resumes/
      // public_id will default to filename without extension (optional)
    });

    fs.unlinkSync(req.file.path);
    res.json({ url: result.secure_url });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
