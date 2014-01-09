'''

David Lettier (C) 2014.

Web server that listens for HTTP requests and servers files.

Requires Python 2.7.3.

'''

import socket;
import threading;
import string;
import ctypes;
import time;
import os;
import mimetypes;
import sys;

# The root directory.

DOCUMENT_ROOT = "./public_html/";

# Client thread class for handling the client sockets.

class Client_Thread( threading.Thread ):
	
	def __init__( self, IP, port, cSocket ):
	
		# Initialize the thread.
	
		threading.Thread.__init__( self );
		
		# System call to get the actual thread ID.
		
		SYS_gettid = 186;
		
		libc = ctypes.cdll.LoadLibrary( "libc.so.6" );
		
		self.thread_id = libc.syscall( SYS_gettid );
		
		# IP address of the socket.
		
		self.IP = IP;
		
		# Port number of the socket.
		
		self.port = port;
		
		# The client socket.
		
		self.client_socket = cSocket;
		
	def run( self ):
	
		# Thread run method.
		
		# Get the request and the headers.
		# Should be:
		# GET /some.file HTTP/1.1 or GET /some.file HTTP/1.0
		# Host: header
		# Bunch
		# Of
		# Other
		# Headers
		# \r\n
		
		query = b'';
		
		while 1:

			buffer = self.client_socket.recv( 1024 );

			if ( buffer.find( "\r\n\r\n" ) != -1 ): 
	
				query = query + buffer;
				
				break;
				
			else:
			
				query = query + buffer;
				
		# Are they using HTTP/1.1?
				
		using_http_1_1 = False;
				
		if ( query.find( "HTTP/1.1" ) != -1 ):
		
			# They are using HTTP/1.1 .
			
			using_http_1_1 = True;
			
		# If they are using HTTP/1.1 then they must
		# send the Host: header.
		
		host_line = query.find( "Host:" );
		
		# Maybe they used lowercase?
		
		if ( host_line == -1 ):
		
			host_line = query.find( "host:" );
			
		# Parse the request and headers.
		
		query = query.split( "\n" );
		
		query_lines = [ ];
		
		for line in query:

			line = line.split( "\r" );
			
			line = line[ 0 ];
			
			query_lines.append( line );
			
		query_lines = filter( None, query_lines );
			
		for line in query_lines:
		
			print "[CLIENT " + str( self.thread_id ) + "] " + line;
			
		print "\n";
		
		if ( not using_http_1_1 or ( using_http_1_1 and host_line != -1 ) ):
		
			# Get the file they are requesting.
		
			query_lines[ 0 ] = query_lines[ 0 ].replace( "GET /", "" );
			query_lines[ 0 ] = query_lines[ 0 ].replace( " HTTP/1.1", "" );
			query_lines[ 0 ] = query_lines[ 0 ].replace( " HTTP/1.0", "" );
			
			# If there is no file assume they want the index.html file.
			
			if ( query_lines[ 0 ] == "" ):
			
				query_lines[ 0 ] = "index.html";
				
			# Try to locate/open the file.
		
			try:
		
				# Get the mime type of the file (text, image, etc.).
				
				content_type = mimetypes.guess_type( DOCUMENT_ROOT + query_lines[ 0 ] )[ 0 ];
				
				# If the file they want is not a image.
				
				if ( content_type.find( "image" ) == -1 ):
				
					# Get the size of the file in bytes.
				
					content_length = os.path.getsize( DOCUMENT_ROOT + query_lines[ 0 ] );
					
					# Open the file an read in the lines.
				
					data_file = open( DOCUMENT_ROOT + query_lines[ 0 ], "r" );
			
					data_file_lines = [ ];
		
					line = data_file.readline( );
		
					while line != "":
		
						data_file_lines.append( line );
			
						line = data_file.readline( );
			
					data_file_lines = "".join( data_file_lines );
					
					# Get the time stamp.
		
					time_stamp = "Date: " + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime( ) );
					
					# Formulate the response.
		
					response = "HTTP/1.1 200 OK" + "\r\n" + time_stamp + "\r\n" + "Content-type: " + content_type + "\r\n" + "Content-length: " + str( content_length ) + "\r\n" + "\r\n" + data_file_lines;
					
					# Send it.
		
					self.client_socket.send( response );
					
					# Print out what the server sent.
					
					response = response.split( "\n" );
					response = filter( None, response );
					
					for line in response:
					
						print "[SERVER] " + line;
						
					# Close the file.
					
					data_file.close( );
					
					# Close the socket.
		
					self.client_socket.close( );
					
				else:
				
					# The file they want is an image so send them the binary data.
					
					# File size.
					
					content_length = os.path.getsize( DOCUMENT_ROOT + query_lines[ 0 ] );
				
					data_file = open( DOCUMENT_ROOT + query_lines[ 0 ], "rb" );
					
					# Time stamp.
		
					time_stamp = "Date: " + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime( ) );
					
					# First part of the response.
		
					response = "HTTP/1.1 200 OK" + "\r\n" + time_stamp + "\r\n" + "Content-type: " + content_type + "\r\n" + "Content-length: " + str( content_length ) + "\r\n" + "\r\n";
		
					self.client_socket.send( response );
					
					# Print out first part of the response.
					
					response = response.split( "\n" );
					response = filter( None, response );
					
					for line in response:
					
						print "[SERVER] " + line;
						
					# Send the binary data of the image.
					
					while 1:
					
						bytes = data_file.read( 1024 );
						
						if not bytes: 
						
							break;
							
						self.client_socket.send( bytes );
						
					print "[SERVER] " + "<binary>";
					
					# Close file and socket.
					
					data_file.close( );
		
					self.client_socket.close( );
			
			except ( IOError, OSError, AttributeError ) as error:
			
				# File not found so send a 404.
		
				print "File not found: " + query_lines[ 0 ] + "\n";
		
				time_stamp = "Date: " + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime( ) );
						
				response_body = "<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<title>404 Not Found</title>\n\t</head>\n\t<body>\n\t\t404 Not Found\n\t</body>\n</html>";
				
				content_length = sys.getsizeof( response_body );
				
				response = "HTTP/1.1 404 Not Found" + "\r\n" + "\r\n" + "File not found.";
			
				self.client_socket.send( response );
				
				# Print out the response.
				
				response = response.split( "\n" );
				response = filter( None, response );
					
				for line in response:
				
					print "[SERVER] " + line;
					
				# Close socket.
		
				self.client_socket.close( );
				
		else:
		
			# They're using HTTP/1.1 but no Host: header was found.
			# Send bad request response.
			
			print "No Host: header found.\n";
			
			time_stamp = "Date: " + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime( ) );
			
			response_body = "<html>\n\t<head>\n\t\t<title>No Host: Header</title>\n\t<body>\n\t\tNo Host: header received.\n\t\tHTTP 1.1 requests must include the Host: header.\n\t</body>\n</html>";
			
			content_length = sys.getsizeof( response_body );
			
			response = "HTTP/1.1 400 Bad Request\n" + time_stamp + "\n" + "Content-Type: text/html\nContent-Length: " + str( content_length ) + "\n\n" + response_body;
			
			self.client_socket.send( response );
			
			response = response.split( "\n" );
			response = filter( None, response );
					
			for line in response:
			
				print "[SERVER] " + line;
				
			# Close socket.
		
			self.client_socket.close( );
			
print "\nWelcome to Web Waiter 9000!\n";

# Setup socket and begin listening for requests.

host = socket.gethostname( ); # Local host name. Should be the name of your machine.
port = 8080;

server_socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM );

server_socket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 );

server_socket.bind( ( host, port ) );

server_socket.listen( 5 );

print "\nServer listening on: " + socket.gethostbyname( socket.gethostname( ) ) + ":" + str( port ) + "\n";

# Handle request as they come in by passing them off to a thread.

while 1:

	# Accept the request.

	( client_socket, ( IP, port ) ) = server_socket.accept( );

	print "\nNew client connection.\n";
	
	# Initialize the thread and run it.

	client_thread = Client_Thread( IP, port, client_socket );

	client_thread.start( );
