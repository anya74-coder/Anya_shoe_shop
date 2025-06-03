// Специфичная валидация для товаров
console.log('Product validation JS loaded');

document.addEventListener('DOMContentLoaded', function() {
    const brandInput = document.querySelector('input[name="brand"]');
    if (brandInput) {
        brandInput.addEventListener('blur', function() {
            const value = this.value.toLowerCase();
            const forbidden = ['test', 'тест', 'fake', 'подделка'];
            
            if (forbidden.some(word => value.includes(word))) {
                this.setCustomValidity('Название содержит недопустимые слова');
            } else {
                this.setCustomValidity('');
            }
        });
    }
});