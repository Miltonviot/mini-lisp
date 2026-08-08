(begin
  (set estoque 4)
  (if (< estoque 5)
    (print 1)
    (print 0))
  (while (> estoque 0)
    (begin
      (print estoque)
      (set estoque (- estoque 1))))
)
