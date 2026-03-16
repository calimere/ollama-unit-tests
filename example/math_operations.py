"""
Exemple de module Python pour tester le générateur de tests
"""

import math
from typing import List, Optional


class Calculator:
    """Calculatrice simple avec différentes opérations"""
    
    def __init__(self, precision: int = 2):
        self.precision = precision
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        """Addition de deux nombres"""
        result = round(a + b, self.precision)
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Soustraction de deux nombres"""
        result = round(a - b, self.precision)
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiplication de deux nombres"""
        result = round(a * b, self.precision)
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Division de deux nombres"""
        if b == 0:
            raise ValueError("Division par zéro impossible")
        result = round(a / b, self.precision)
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """Calcul de puissance"""
        result = round(base ** exponent, self.precision)
        self.history.append(f"{base} ^ {exponent} = {result}")
        return result
    
    def square_root(self, x: float) -> float:
        """Racine carrée"""
        if x < 0:
            raise ValueError("Racine carrée d'un nombre négatif")
        result = round(math.sqrt(x), self.precision)
        self.history.append(f"√{x} = {result}")
        return result
    
    def get_history(self) -> List[str]:
        """Retourne l'historique des calculs"""
        return self.history.copy()
    
    def clear_history(self):
        """Efface l'historique"""
        self.history.clear()


def factorial(n: int) -> int:
    """Calcule la factorielle d'un nombre"""
    if not isinstance(n, int):
        raise TypeError("n doit être un entier")
    if n < 0:
        raise ValueError("n doit être positif ou nul")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


def fibonacci(n: int) -> int:
    """Calcule le n-ième nombre de Fibonacci"""
    if not isinstance(n, int):
        raise TypeError("n doit être un entier")
    if n < 0:
        raise ValueError("n doit être positif ou nul")
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)


def is_prime(n: int) -> bool:
    """Vérifie si un nombre est premier"""
    if not isinstance(n, int):
        raise TypeError("n doit être un entier")
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def find_gcd(a: int, b: int) -> int:
    """Trouve le plus grand commun diviseur de deux nombres"""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("a et b doivent être des entiers")
    
    a, b = abs(a), abs(b)
    if a == 0:
        return b
    if b == 0:
        return a
    
    while b:
        a, b = b, a % b
    return a


class Statistics:
    """Classe pour calculer des statistiques sur une liste de nombres"""
    
    def __init__(self, data: Optional[List[float]] = None):
        self.data = data or []
    
    def add_value(self, value: float):
        """Ajoute une valeur à la liste"""
        if not isinstance(value, (int, float)):
            raise TypeError("La valeur doit être un nombre")
        self.data.append(float(value))
    
    def mean(self) -> float:
        """Calcule la moyenne"""
        if not self.data:
            raise ValueError("Aucune donnée disponible")
        return sum(self.data) / len(self.data)
    
    def median(self) -> float:
        """Calcule la médiane"""
        if not self.data:
            raise ValueError("Aucune donnée disponible")
        
        sorted_data = sorted(self.data)
        n = len(sorted_data)
        
        if n % 2 == 0:
            return (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2
        else:
            return sorted_data[n // 2]
    
    def variance(self) -> float:
        """Calcule la variance"""
        if len(self.data) < 2:
            raise ValueError("Au moins deux valeurs requises")
        
        mean_val = self.mean()
        return sum((x - mean_val) ** 2 for x in self.data) / (len(self.data) - 1)
    
    def standard_deviation(self) -> float:
        """Calcule l'écart-type"""
        return math.sqrt(self.variance())
    
    def min_value(self) -> float:
        """Retourne la valeur minimale"""
        if not self.data:
            raise ValueError("Aucune donnée disponible")
        return min(self.data)
    
    def max_value(self) -> float:
        """Retourne la valeur maximale"""
        if not self.data:
            raise ValueError("Aucune donnée disponible")
        return max(self.data)


# Constantes
PI = math.pi
E = math.e
GOLDEN_RATIO = (1 + math.sqrt(5)) / 2