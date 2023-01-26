from bs4 import BeautifulSoup as bs

source_file = "/home/rpw/RarePepeWorld/rpw/static/data/faq.xml"
with open(source_file, 'r') as f:
    faq_content = bs(''.join(f.readlines()), 'lxml')

faq_items = faq_content.find('questions').find_all('faq-item')
for faq_item in faq_items:
    question_tag = ''.join(str(s) for s in faq_item.find('question').children).replace('\n','')
    answer_tag = ''.join([str(s) for s in faq_item.find('answer').children]).replace('\n','')
    print("\n=====FAQ-ITEM======")
    print("\n=====Question======")
    print(question_tag)
    print("\n=====Answer======")
    print(answer_tag)
#     # question = faq_item.find('question').text
#     # answer = faq_item.find('answer').text
#     # print(question)
#     # print(answer)
