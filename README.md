# Lokalizacja robota w świecie Wumpusa - projekt z przedmiotu SIwR

Zadanie polegało na uzupełnieniu kodu tak, aby robot potrafił się sam lokalizować w nieznanym świecie. Ponadto należało stworzyć heurystykę, która pozwalała na lepszy proces lokalizacji stanu robota. Robot posiada również mapę otoczenia oraz określone zasady według których może poruszać się w przestrzeni. 

### 1 część zadania - uzupełnianie macierzy self.P wartościami prawdopodobieństw, które określały najbardziej prawdopodobne stany robota

Podstawowym elementem zadania było stworzenie listy stanów **self.states**, która oprócz lokalizacji zawierała również odpowiednie kierunki obrotu robota.
Za rozkład prawdopodobieństwa związanego z ruchem robota, odpowiada macierz **self.t** 
o wymiarach 168x168.

Za dane związane z odczytem z sensorów odpowiada macierz **self.o** o wymiarach 168x1.
Macierz **self.P** w której znajdują się prawdopodobieństwa wszystkich stanów robota, została zainicjalizowana wartością 1/168 dla każdego pola i jest odpowiednio nadpisywana za pomocą macierzy self.t i self.o oraz normalizowana.

```python
  # Obliczanie self.P
  self.temp = self.t.transpose() @ self.P
  self.P = self.O * self.temp
  self.P /= np.sum(self.P)
```
Interesującym momentem zawartym w kodzie jest funkcja **global_orient** zadeklarowana w pliku **gridutil.py**, która zamienia lokalne odczyty sensorów na globalny odczyt, co pozwala na ich łatwiejsze porównanie i zapis prawdopodobieństw do macierzy self.o. 

### 2 część zadania - stworzenie heurystyki, która polepszała samolokalizowanie się robota

Kolejnym elementem projektu było stworzenie heurystyki, która pozwalałaby na lepszą zdolność robota do samolokalizacji.
Wybrana przeze mnie strategia jest następująca:
- Przez 10 pierwszych kroków robot porusza się z dużą dozą losowości, jednak preferuje on ruch naprzód. Wynika to z obserwacji, że taki ruch pozwala robotowi na zdobywanie       większej ilości informacji niż podczas obrotu. Liczba akcji została dobrana doświadczalnie ze względu na fakt, iż po tylu iteracjach robot potrafił ograniczyć zwykle swoje położenie do maksymalnie 3 stanów. W tej części algorytmu robot korzysta jedynie z odczytów swoich sensorów, które mogą pokazywać błędne pomiary.

- Po wykonaniu pierwszych dziesięciu ruchów, na podstawie macierzy self.P zostaje wybrany stan robota o największym prawdopodobieństwie i to dla niego planowany jest dalszy       ruch. Polega on na poruszaniu się robota wzdłuż prawej ściany. Umożliwia to odwiedzenie po kolei wszystkich lokacji w dużo szybszym czasie niż dla losowych ruchów, co pozwala na lepszą eksplorację otoczenia.
  - Ograniczenie ruchów robota zostało dobrane na podstawie obserwacji jego zachowania i zaimplementowane za pomocą instrukcji warunkowej.
  - Robot wykonuje ruchy na podstawie listy stanów, do której dopisuje kolejne akcje.
  - W momencie gdy lista akcji pozostaje pusta (elementy są z niej pobierane za pomocą komendy **pop(0)**) lub robot natrafił na ścianę (**bump** - wybrany stan nie jest         poprawny), robot weryfikuje swój stan i sprawdza czy znajduje się w najbardziej prawdopodobnym stanie. Jeśli nie to zmienia on swój stan.
  - Weryfikacja najbardziej prawdopodobnego stanu robota została zaimplementowana w metodzie **find_state** zawartej w pliku **prob.py**.
  ```python
      def find_state(self):
        index = 0
        key = None
        maximum = np.max(self.P)
        lista = self.P.tolist()
        for element in lista:
            if element == maximum:
                index = lista.index(element)
        for state, value in self.state_to_idx.items():
            if value == index:
                key = state
        return key
    ```
  - Weryfikacja stanu maksymalnie po 2 akcjach pozwala również na większą odporność heurystyki w sytuacjach, gdy robot nie poruszył się lub nie obrócił.
  - Ponadto jeżeli robot znalazł już prawidłową lokalizację i orientację, to będzie się jej trzymał. Przyczyną tego jest odkrywanie kolejnych lokacji na mapie oraz weryfikacja stanu robota po wyczerpaniu się akcji w liście **self.action_list**.
  - W heurystyce zakładamy również że robot zna mapę, ponieważ korzysta z niej aby sprawdzić gdzie są ściany dla najbardziej prawdopodobnego stanu i zaplanować swoją kolejną akcję. Sprawdzenie to odbywa się w metodzie **check_real_walls** zawartej w pliku **prob.py**.
  - Algorytm posiada również wadę. Jest nią wpadanie w cykl, z którego robot nie może wyjść w niektórych stanach. Aby temu zapobiec została dodana możliwość wyboru kierunku obrotu dla tych stanów z odpowiednim prawdopodobieństwem. 

Kod został opatrzony odpowiednimi komentarzami. W razie pytań proszę o kontakt. 
