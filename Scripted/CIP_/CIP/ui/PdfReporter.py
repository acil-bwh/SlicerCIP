import qt

import os
import shutil
import logging
import tempfile


class PdfReporter(object):
    def __init__(self):
        self.htmlTemplate = None
        self.__pdfOutputPath__ = None
        self.__callbackFunction__ = None
        self.__finalHtmlPath__ = None


    def printPdf(self, htmlTemplatePath, values, callbackFunction, pdfOutputPath=None,
                 imagesFileList=None, tempHtmlFolder=None,):
        """
        Print a pdf file with the html stored in htmlPath and the specified values
        :param htmlTemplatePath: path to the html file that contains the template
        :param values: dictionary of values that will be used to build the final html
        :param callbackFunction: function that will be called when the process has finished (it is an asynchronous process)
        :param pdfOutputPath: path to the pdf file that will be created (if none, it will be saved in a temp file)
        :param imagesFileList: list of full paths to images that may be needed to generate the report
        :param tempHtmlFolder: folder where all the intermediate files will be stored. If none, a temporary folder will be used
        """
        if tempHtmlFolder is None:
            tempHtmlFolder = tempfile.mkdtemp()

        self.__pdfOutputPath__ = pdfOutputPath if pdfOutputPath is not None else os.path.join(tempHtmlFolder, "report.pdf")
        self.__callbackFunction__ = callbackFunction

        # Generate the Html
        with open(htmlTemplatePath, "r") as f:
            html = f.read()
        for key, value in values.items():
            html = html.replace(key, value)

        # If we need images, copy them to the temporary folder
        if imagesFileList:
            for im in imagesFileList:
                fileName = os.path.basename(im)
                shutil.copy(im, os.path.join(tempHtmlFolder, fileName))

        if hasattr(qt,'QWebView'):
            # Save the file in the temporary folder
            htmlPath = os.path.join(tempHtmlFolder, "temp__.html")
            with open(htmlPath, "w") as f:
                f.write(html)
            logging.debug("Html generated in {}".format(htmlPath))
            # Create a web browser for rendering html
            self.webView = qt.QWebView()
            self.webView.settings().setAttribute(qt.QWebSettings.DeveloperExtrasEnabled, True)
            self.webView.connect('loadFinished(bool)', self.__webViewFormLoadedCallback__)
            u = qt.QUrl(htmlPath)
            self.webView.setUrl(u)
            self.webView.show()
        else:
            printer = qt.QPrinter(qt.QPrinter.PrinterResolution)
            printer.setOutputFormat(qt.QPrinter.PdfFormat)
            printer.setPaperSize(qt.QPrinter.A4)
            printer.setOutputFileName(self.__pdfOutputPath__)

            doc = qt.QTextDocument()
            doc.setHtml(html)
            doc.baseUrl = qt.QUrl.fromLocalFile(tempHtmlFolder+"/")
            doc.setPageSize(qt.QSizeF(printer.pageRect().size()))  # hide the page number
            doc.print(printer)

            # Call the callback
            self.__callbackFunction__(self.__pdfOutputPath__)
            self.__callbackFunction__ = None

    def __webViewFormLoadedCallback__(self, loaded):
        if loaded:
            #outputFileName = os.path.join(self.getCurrentDataFolder(), "report.pdf")
            printer = qt.QPrinter(qt.QPrinter.HighResolution)
            printer.setOutputFormat(qt.QPrinter.PdfFormat)
            printer.setOutputFileName(self.__pdfOutputPath__)
            self.webView.print_(printer)
            self.webView.close()
            # Call the callback
            self.__callbackFunction__(self.__pdfOutputPath__)
            self.__callbackFunction__ = None
