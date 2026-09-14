def mutate(dictionary):
    dictionary["mutate"] = "mutate"

if __name__ == '__main__':
    dictionary = {}
    mutate(dictionary)
    print(dictionary)