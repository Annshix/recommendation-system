#import dataGenerate      generate data
import math
import Params
from operator import itemgetter
import sys
import json
import zipfile
import random

class ItemBasedRec:
    def __init__(self, item, weighted_relation, rec_num):
        self.item = item
        self.weightedRelation = weighted_relation
        self.recNum = rec_num
        self.recNum_1 = round(rec_num * Params.lambda_fav1)
        self.recNum_2 = round(rec_num * Params.lambda_fav2)
        self.weight = dict()

    def item_similarity(self):
        cor, popularity = dict(), dict()
        for user, items in self.weightedRelation.items():
            for i in items.keys():
                popularity.setdefault(i, 0)
                popularity[i] += 1
                cor.setdefault(i, {})
                for j in items.keys():
                    if i != j:
                        cor[i].setdefault(j, 0)
                        cor[i][j] += items[i] * items[j]
        theta = 0
        for k, v in cor.items():
            for vv in v.values():
                theta += vv
        theta = theta / math.pow(len(cor), 2) * Params.THETA
        for i, related_items in cor.items():
            self.weight.setdefault(i, {})
            for j, cij in related_items.items():
                self.weight[i][j] = cij
                if i in self.item.keys() and j in self.item.keys():
                    for region_i in range(3):
                        for region_j in range(3):
                            if self.item[i][region_i + 3] == self.item[j][region_j + 3]:
                                thred = min(int(self.item[i][2]), int(self.item[j][2])) - min(region_i, region_j)
                                if thred > 0:
                                    self.weight[i][j] += theta * thred * 2
                    if self.item[i][1] and self.item[i][1] == self.item[j][1]:
                        self.weight[i][j] += theta * 3
                self.weight[i][j] /= (math.sqrt(popularity[i] * popularity[j]))

    def recommend(self):
        for user in self.weightedRelation.keys():
            rank = dict()
            item_set = self.weightedRelation[user]
            category, prov = dict(), dict()
            for item, weight in item_set.items():
                if item in self.item.keys():
                    counts = 0
                    for j, wj in sorted(self.weight[item].items(), key=itemgetter(1), reverse=True):
                        if j in self.item.keys() and self.item[j][6] == '0' and j not in item_set.keys():
                            counts += 1
                            rank.setdefault(j, 0)
                            rank[j] += weight * wj
                        if counts == self.recNum * 2:
                            break
                    category.setdefault(self.item[item][1], 0)
                    category[self.item[item][1]] += weight
                    index = int(self.item[item][2])+2
                    prov.setdefault(self.item[item][index], 0)
                    prov[self.item[item][index]] += weight

            # x% recommendation from ranking
            item_fav = list(map(lambda x: x[0], sorted(rank.items(), key = itemgetter(1), reverse = True)[0: self.recNum_1]))
            self.weightedRelation[user]["rank"] = item_fav[: self.recNum_1]
        
            # y% recommendation from ranking by random choice
            item_fav2_temp = item_fav[self.recNum_1:self.recNum_1 * 2]
            if len(item_fav2_temp):
                while len(self.weightedRelation[user]["rank"]) < self.recNum_2:
                    item_new = random.choice(item_fav2_temp)
                    self.weightedRelation[user]["rank"].append(item_new)

            # z% recommendation by random choice
            max_category = max(category.items(), key = itemgetter(1))[0]
            max_prov = max(prov.items(), key = itemgetter(1))[0]
            rand_choice = list()        
            if max_category and max_prov:
                for item, details in self.item.items():
                    if details[6] == '0' and item not in item_set.keys() and item not in self.weightedRelation[user]["rank"] and (details[1] == max_category or details[int(details[2]) + 2] == max_prov):
                        rand_choice.append(item)
                while len(self.weightedRelation[user]["rank"]) < self.recNum:
                    item_random = random.choice(rand_choice)
                    self.weightedRelation[user]["rank"].append(item_random)
                    rand_choice.remove(item_random)
                else:
                    break

def main():
    if len(sys.argv) == 2 and sys.argv[1] == 'test':
        rs = dataGenerate.DataGenerate(False)
    elif len(sys.argv) == 1:
        rs = dataGenerate.DataGenerate(True)
    else:
        return
    print('Finish Loading!')

    rankrec = ItemBasedRec(rs.item, rs.weightedRelation, rec_num=100)
    rankrec.item_similarity()
    rankrec.recommend()
    for u, d in rankrec.weightedRelation.items():
        if 'rank' not in d:
            print(u)
            print(d)

    if sys.path[0]:
        file_path = sys.path[0] + '/'
    else:
        file_path = sys.path[0]

    with open(file_path + Params.FILETRANSFORM, 'w') as f:
        for user, detail in rankrec.weightedRelation.items():
            print(1)
            print(detail['rank'])
            f.write(str(user) + ':' + ','.join(detail['rank']) + '\n')

    with zipfile.ZipFile(Params.DATA_DIR + Params.FILETRANSFORM_ZIP,'w')  as json_zip:
        json_zip.write(file_path + Params.FILETRANSFORM,arcname = Params.FILETRANSFORM)

    print('Finish Recommending!')

    return


if __name__ == "__main__":
    main()

