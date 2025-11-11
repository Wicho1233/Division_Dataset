// JavaScript para mejoras de UX
document.addEventListener('DOMContentLoaded', function() {
    // Validación de tamaños
    const trainSize = document.getElementById('id_train_size');
    const valSize = document.getElementById('id_val_size');
    const testSize = document.getElementById('id_test_size');
    
    function validateSizes() {
        const total = parseFloat(trainSize.value) + parseFloat(valSize.value) + parseFloat(testSize.value);
        const warning = document.getElementById('size-warning');
        
        if (!warning) {
            const div = document.createElement('div');
            div.id = 'size-warning';
            div.className = 'alert alert-warning mt-2';
            testSize.parentNode.appendChild(div);
        }
        
        if (Math.abs(total - 1.0) > 0.01) {
            document.getElementById('size-warning').textContent = 
                `La suma de los tamaños es ${total.toFixed(2)}. Se normalizará a 1.0.`;
            document.getElementById('size-warning').style.display = 'block';
        } else {
            document.getElementById('size-warning').style.display = 'none';
        }
    }
    
    if (trainSize && valSize && testSize) {
        [trainSize, valSize, testSize].forEach(input => {
            input.addEventListener('change', validateSizes);
            input.addEventListener('input', validateSizes);
        });
    }
    
    // Mejora para el input de archivo
    const fileInput = document.getElementById('id_dataset_file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'No se seleccionó archivo';
            const fileInfo = document.getElementById('file-info') || document.createElement('div');
            fileInfo.id = 'file-info';
            fileInfo.className = 'file-info';
            fileInfo.textContent = `Archivo seleccionado: ${fileName}`;
            
            if (!document.getElementById('file-info')) {
                fileInput.parentNode.appendChild(fileInfo);
            }
        });
    }
});