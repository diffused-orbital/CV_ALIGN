app.post('/upload/job-description/:company', upload.single('file'), async (req, res) => {
  const company = req.params.company;

  try {
    const result = await cloudinary.uploader.upload(req.file.path, {
      resource_type: 'raw',             // Required for PDFs/DOCs
      folder: `${company}`,             // e.g., CompanyA/
      public_id: 'job_description'      // Fixed name, will overwrite if re-uploaded
    });

    fs.unlinkSync(req.file.path);       // Delete local temp file
    res.json({ url: result.secure_url }); // Return cloud URL
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});
