
Welcome to QNntp's documentation!
*********************************

Contents:

class class qnntp.QNntp(parent=None)

   -[ Methods ]-

   article(descriptor='')

      Perform an "ARTICLE" command.

      Parameters :
         **descriptor** : str, optional

            message-id or article number

      Emits :
         **articleReady** : on success

   body(descriptor='')

      Perform a "BODY" command.

      Parameters :
         **descriptor** : str, optional

            message-id or article number

      Emits :
         **bodyReady** : on success

   connectToHost(host, port=119)

      Connect to host.

      Parameters :
         **host** : str

         **port** : int, optional

   group(name)

      Perform a "GROUP" command.

      Parameters :
         **name** : str

      Emits :
         **groupReady** : on success

   head(descriptor='')

      Perform a "HEAD" command.

      Parameters :
         **descriptor** : str, optional

            message-id or article number

      Emits :
         **headReady** : on success

   last()

      Perform a "LAST" command.

      Emits :
         **statReady** : on success

   list(pattern='')

      Perform a "LIST" or "LIST ACTIVE" command.

      Parameters :
         **pattern** : str, optional

      Emits :
         **listReady** : on success

   listgroup(group=None, start=None, end=None)

      Perform a "LISTGROUP" command.

      Parameters :
         **group** : str, optional

         **start** : int, optional

         **end** : int, optional

      Emits :
         **listgroupReady** : on success

   next()

      Perform a "NEXT" command.

      Emits :
         **statReady** : on success

   stat(descriptor='')

      Perform a "STAT" command.

      Parameters :
         **descriptor** : str, optional

            message-id or article number

      Emits :
         **statReady** : on success

      See also:

         "next()", "last()"
